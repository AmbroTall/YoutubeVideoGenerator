from datetime import datetime, timezone
import yt_dlp
from pymongo import MongoClient
import time
from apscheduler.schedulers.background import BackgroundScheduler
import traceback
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class YouTubeScanner:
    def __init__(self, mongodb_uri):
        self.client = MongoClient(mongodb_uri)
        logger.info("Connected to MongoDB at: %s", mongodb_uri)
        
        self.db = self.client['youtube_shorts']
        self.processed_videos = self.db['processed_videos']
        self.channel_info = self.db['channel_info']
        
        try:
            self.client.admin.command('ping')
            logger.info("✓ MongoDB connection successful")
            logger.info("Available databases: %s", self.client.list_database_names())
            logger.info("Collections in youtube_shorts: %s", self.db.list_collection_names())
        except Exception as e:
            logger.error("❌ MongoDB connection error: %s", str(e))
            raise
        
        self.scheduler = BackgroundScheduler()
        self.api_key = 'AIzaSyAFm2OMY-fMQyyc4rdPoNsEPbgNtCf-3X8'

    def _parse_duration(self, duration_str):
        """Parse ISO 8601 duration to seconds"""
        match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration_str)
        if not match:
            return 0
        hours = int(match.group(1)[:-1]) if match.group(1) else 0
        minutes = int(match.group(2)[:-1]) if match.group(2) else 0
        seconds = int(match.group(3)[:-1]) if match.group(3) else 0
        return hours * 3600 + minutes * 60 + seconds

    def initialize_channel(self, initial_video_url):
        """Initialize channel tracking from an initial video"""
        try:
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(initial_video_url, download=False)
                channel_id = info['channel_id']
                
                upload_date = info['upload_date']
                formatted_date = (
                    f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}T00:00:00Z"
                    if len(upload_date) == 8
                    else upload_date
                )
                
                self.channel_info.update_one(
                    {'_id': channel_id},
                    {
                        '$set': {
                            'channel_name': info['channel'],
                            'initial_video_date': formatted_date,
                            'last_scan': datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
                
                self.processed_videos.update_one(
                    {'video_id': info['id']},
                    {
                        '$set': {
                            'channel_id': channel_id,
                            'upload_date': formatted_date,
                            'processed_date': datetime.now(timezone.utc),
                            'video_processed': False
                        }
                    },
                    upsert=True
                )
                
                return channel_id
        except Exception as e:
            print(f"Error initializing channel: {e}")
            return None

    def get_new_shorts(self, channel_id):
        """Get new Videos from channel using YouTube Data API"""
        try:
            logger.info("\n====== Starting New Videos Check for %s ======", channel_id)
            
            last_processed = self.processed_videos.find_one(
                {'channel_id': channel_id},
                sort=[('upload_date', -1)]
            )
            
            # Create YouTube API client without file cache
            youtube = build(
                'youtube', 
                'v3', 
                developerKey=self.api_key,
                cache_discovery=False  # Disable discovery doc caching
            )
            
            # Get recent videos from channel
            search_response = youtube.search().list(
                part="id",
                channelId=channel_id,
                maxResults=10,
                type="video",
                order="date"
            ).execute()
            
            videos = search_response.get('items', [])
            if not videos:
                logger.info("No videos found")
                return []
                
            video_ids = [item['id']['videoId'] for item in videos]
            
            # Get detailed video information
            details_response = youtube.videos().list(
                part="contentDetails,snippet",
                id=','.join(video_ids)
            ).execute()
            
            qualifying_videos = []
            
            for video in details_response.get('items', []):
                try:
                    video_id = video['id']
                    duration = self._parse_duration(video['contentDetails']['duration'])
                    upload_date = video['snippet']['publishedAt']
                    title = video['snippet']['title']
                    
                    # Skip if already processed
                    if self.processed_videos.find_one({'video_id': video_id}):
                        continue
                        
                    # Check if newer than last processed
                    if last_processed:
                        video_date = datetime.strptime(upload_date, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        last_processed_date = last_processed['upload_date']
                        
                        # Ensure last_processed_date is a datetime object
                        if isinstance(last_processed_date, str):
                            last_processed_date = datetime.strptime(last_processed_date, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        
                        # Ensure both dates are timezone aware
                        if last_processed_date.tzinfo is None:
                            last_processed_date = last_processed_date.replace(tzinfo=timezone.utc)

                        if video_date <= last_processed_date:
                            continue
                    
                    qualifying_videos.append({
                        'id': video_id,
                        'title': title,
                        'upload_date': upload_date,
                        'duration': duration,
                        'channel_id': channel_id,
                        'video_processed': False
                    })
                    
                except Exception as e:
                    logger.error("Error processing video %s: %s", video_id, str(e))
                    continue
            
            # Sort by upload date and return oldest
            if qualifying_videos:
                qualifying_videos.sort(key=lambda x: x['upload_date'])
                return [qualifying_videos[0]]
            
            return []
            
        except Exception as e:
            logger.error("Error checking for new shorts: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return []

    def process_shorts(self, videos):
        """Process new videos"""
        if not videos:
            logger.info("No videos to process")
            return

        try:
            video = videos[0]
            logger.info("Processing video %s", video['id'])
            
            # Double-check not already processed
            if self.processed_videos.find_one({'video_id': video['id']}):
                logger.info("Video %s already processed, skipping", video['id'])
                return
            
            # Add to processed videos collection
            video_data = {
                'video_id': video['id'],
                'title': video['title'],
                'channel_id': video['channel_id'],
                'upload_date': datetime.strptime(video['upload_date'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc),
                'processed_date': datetime.now(timezone.utc),
                'video_processed': False
            }
            
            result = self.processed_videos.insert_one(video_data)
            
            if result.inserted_id:
                logger.info("✓ Successfully processed video %s", video['id'])
            else:
                logger.error("❌ Failed to process video %s", video['id'])
                
        except Exception as e:
            logger.error("Error processing video: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())

    def start_scanning(self, channel_id, callback=None):
        """Start periodic scanning of a channel"""
        try:
            channel = self.channel_info.find_one({'_id': channel_id})
            if not channel:
                logger.error("Channel %s not found in database", channel_id)
                return False

            def scan_job():
                logger.info("\n====== Starting Scan Job for %s ======", channel_id)
                new_shorts = self.get_new_shorts(channel_id)
                
                if new_shorts:
                    self.process_shorts(new_shorts)
                    if callback:
                        callback(new_shorts[0])
                
                self.channel_info.update_one(
                    {'_id': channel_id},
                    {'$set': {'last_scan': datetime.now(timezone.utc)}}
                )

            # Reset scheduler
            if hasattr(self, 'scheduler'):
                self.scheduler.remove_all_jobs()

            # Add new scanning job (every 5 minutes)
            self.scheduler.add_job(
                scan_job,
                'interval',
                minutes=5,
                id=f'scan_{channel_id}'
            )

            # Start the scheduler if it's not running
            if not self.scheduler.running:
                self.scheduler.start()

            # Run immediate scan
            scan_job()
            return True

        except Exception as e:
            logger.error("Error starting scanner: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return False

    def get_channel_info(self, channel_id):
        """Get channel information from database"""
        try:
            channel = self.channel_info.find_one({'_id': channel_id})
            if not channel:
                return None
            
            # Get latest processed video
            latest_video = self.processed_videos.find_one(
                {'channel_id': channel_id},
                sort=[('upload_date', -1)]
            )
            
            # Get total processed videos count
            total_processed = self.processed_videos.count_documents({'channel_id': channel_id})
            
            return {
                'channel_name': channel.get('channel_name', 'Unknown'),
                'initial_video_date': channel.get('initial_video_date'),
                'last_scan': channel.get('last_scan'),
                'latest_video': {
                    'id': latest_video.get('video_id') if latest_video else None,
                    'title': latest_video.get('title') if latest_video else None,
                    'upload_date': latest_video.get('upload_date') if latest_video else None
                } if latest_video else None,
                'total_processed': total_processed
            }
            
        except Exception as e:
            logger.error("Error getting channel info: %s", str(e))
            logger.error("Stack trace: %s", traceback.format_exc())
            return None