"""
Redis Database Module for MindMate Bot
Handles persistent storage with fallback for vector search
"""

import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
import os
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Message data structure"""
    user_id: int
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime
    message_id: str

class RedisDatabase:
    """Redis database manager with basic storage capabilities"""
    
    def __init__(self, redis_url: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.redis_url = redis_url
        self.embedding_model_name = embedding_model
        self.redis_client = None
        self.vector_search_enabled = False
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis connected successfully")
            
            # Try to initialize embedding model (optional)
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                self.vector_dimension = 384
                self.vector_search_enabled = True
                logger.info(f"✅ Vector search enabled: {self.embedding_model_name}")
                
                # Create vector index for semantic search
                await self._create_vector_index()
            except ImportError:
                logger.warning("⚠️ Vector search disabled (sentence-transformers not available)")
                logger.info("🔄 Using keyword search fallback")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def _create_vector_index(self):
        """Create RediSearch vector index for semantic search"""
        if not self.vector_search_enabled:
            return
            
        try:
            # Drop existing index if it exists
            try:
                await self.redis_client.ft("msg_idx").dropindex()
                logger.info("🔄 Dropped existing vector index")
            except:
                pass
            
            # Create new vector index
            await self.redis_client.ft("msg_idx").create_index(
                fields=[
                    redis.fields.TextField("$.content", as_name="content"),
                    redis.fields.VectorField("$.embedding", 
                        "FLAT", 
                        {
                            "TYPE": "FLOAT32",
                            "DIM": self.vector_dimension,
                            "DISTANCE_METRIC": "COSINE"
                        }, 
                        as_name="embedding")
                ]
            )
            logger.info("✅ Vector index created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create vector index: {e}")
            # Continue without vector search if Redis doesn't support it
            logger.warning("⚠️ Continuing without vector search capabilities")
    
    async def store_message(self, message: Message):
        """Store a message in Redis with optional embedding and archiving"""
        try:
            # Store message data
            message_data = {
                "user_id": message.user_id,
                "content": message.content,
                "role": message.role,
                "timestamp": message.timestamp.isoformat(),
                "message_id": message.message_id
            }
            
            # Add embedding if vector search is enabled
            if self.vector_search_enabled:
                try:
                    import numpy as np
                    embedding = self.embedding_model.encode(message.content, convert_to_numpy=True)
                    embedding_list = embedding.astype(np.float32).tolist()
                    message_data["embedding"] = embedding_list
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate embedding: {e}")
            
            # Store in Redis hash
            key = f"message:{message.message_id}"
            await self.redis_client.hset(key, mapping=message_data)
            
            # Add to user's conversation list
            conversation_key = f"conversation:{message.user_id}"
            await self.redis_client.lpush(conversation_key, json.dumps({
                "message_id": message.message_id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            }))
            
            # Trim conversation to last 50 messages (move old ones to archive)
            await self._archive_old_messages(message.user_id, conversation_key)
            
            # Set TTL for conversation (30 days)
            await self.redis_client.expire(conversation_key, 30 * 24 * 3600)
            await self.redis_client.expire(key, 30 * 24 * 3600)
            
            logger.debug(f"✅ Stored message {message.message_id} for user {message.user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store message: {e}")
            raise
    
    async def _archive_old_messages(self, user_id: int, conversation_key: str):
        """Archive messages that would be trimmed from conversation."""
        try:
            # Get messages that would be trimmed (keep only last 50)
            messages = await self.redis_client.lrange(conversation_key, 50, -1)  # Get messages beyond position 50
            
            if messages:
                archive_key = f"archive:{user_id}"
                for msg_json in messages:
                    # Add to archive with extended TTL (90 days)
                    await self.redis_client.lpush(archive_key, msg_json)
                
                # Set longer TTL for archives (90 days vs 30 days)
                await self.redis_client.expire(archive_key, 90 * 24 * 3600)
                
                # Trim conversation to last 50
                await self.redis_client.ltrim(conversation_key, 0, 49)
                
                logger.info(f"📦 Archived {len(messages)} messages for user {user_id}")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to archive messages: {e}")
    
    async def get_archived_messages(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Retrieve archived messages for a user."""
        try:
            archive_key = f"archive:{user_id}"
            messages = await self.redis_client.lrange(archive_key, 0, limit - 1)
            
            archived = []
            for msg_json in messages:
                try:
                    msg_data = json.loads(msg_json)
                    archived.append(msg_data)
                except json.JSONDecodeError:
                    continue
            
            return archived
            
        except Exception as e:
            logger.error(f"❌ Failed to get archived messages: {e}")
            return []
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history for a user"""
        try:
            conversation_key = f"conversation:{user_id}"
            messages = await self.redis_client.lrange(conversation_key, 0, limit - 1)
            
            history = []
            for msg_json in messages:
                try:
                    msg_data = json.loads(msg_json)
                    history.append(msg_data)
                except json.JSONDecodeError:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation history: {e}")
            return []
    
    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Search for semantically similar messages across recent conversation AND archive"""
        try:
            # Check if vector search is enabled
            if not self.vector_search_enabled:
                logger.info("🔄 Using keyword search fallback (vector search disabled)")
                return await self._keyword_search_with_archive(user_id, query, limit)
            
            # First search recent conversation
            recent_results = await self._search_recent_vector(user_id, query, limit)
            
            # If not enough results, search archive too
            if len(recent_results) < limit:
                archive_results = await self._search_archive_keyword(user_id, query, limit - len(recent_results))
                recent_results.extend(archive_results)
            
            return recent_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return await self._keyword_search_with_archive(user_id, query, limit)
    
    async def _search_recent_vector(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Search recent conversation using vector search"""
        try:
            # Generate query embedding
            import numpy as np
            query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
            query_vector = query_embedding.astype(np.float32).tolist()
            
            # Perform vector search
            search_query = f"*=>[KNN {limit} @embedding $query_vec]"
            
            result = await self.redis_client.ft("msg_idx").search(
                redis.Query(search_query).add_param("query_vec", query_vector).return_fields("content", "message_id", "timestamp")
            )
            
            # Filter by user_id and format results
            relevant_messages = []
            for doc in result.docs:
                try:
                    # Get full message data
                    message_data = await self.redis_client.hgetall(f"message:{doc.message_id}")
                    if message_data and int(message_data.get("user_id", 0)) == user_id:
                        relevant_messages.append({
                            "content": message_data["content"],
                            "role": message_data["role"],
                            "timestamp": message_data["timestamp"],
                            "message_id": message_data["message_id"],
                            "source": "recent",
                            "similarity": 1 - float(doc.__dict__.get("score", 0))  # Convert distance to similarity
                        })
                except Exception as e:
                    logger.debug(f"Error processing search result: {e}")
                    continue
            
            return relevant_messages[:limit]
            
        except Exception as e:
            logger.warning(f"⚠️ Vector search failed: {e}")
            return []
    
    async def _search_archive_keyword(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Search archived messages using keyword matching"""
        try:
            archive_key = f"archive:{user_id}"
            archived_messages = await self.redis_client.lrange(archive_key, 0, -1)
            
            archive_results = []
            query_lower = query.lower()
            
            for msg_json in archived_messages:
                try:
                    msg_data = json.loads(msg_json)
                    content = msg_data.get("content", "").lower()
                    
                    # Simple keyword matching
                    if any(word in content for word in query_lower.split() if len(word) > 2):
                        archive_results.append({
                            "content": msg_data.get("content", ""),
                            "role": msg_data.get("role", ""),
                            "timestamp": msg_data.get("timestamp", ""),
                            "source": "archive",
                            "similarity": 0.7  # Default score for keyword matches
                        })
                except json.JSONDecodeError:
                    continue
            
            # Sort by timestamp (most recent first) and limit
            archive_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return archive_results[:limit]
            
        except Exception as e:
            logger.warning(f"⚠️ Archive search failed: {e}")
            return []
    
    async def _keyword_search_with_archive(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Keyword search across both recent and archived messages"""
        try:
            # Search recent first
            recent_results = await self._keyword_search(user_id, query, limit)
            
            # If not enough results, search archive
            if len(recent_results) < limit:
                archive_results = await self._search_archive_keyword(user_id, query, limit - len(recent_results))
                recent_results.extend(archive_results)
            
            return recent_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Keyword search with archive failed: {e}")
            return []
    
    async def _keyword_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Fallback keyword search in conversation history"""
        try:
            history = await self.get_conversation_history(user_id, limit=50)
            
            # Simple keyword matching
            query_lower = query.lower()
            relevant_messages = []
            
            for msg in history:
                if query_lower in msg["content"].lower():
                    relevant_messages.append({
                        **msg,
                        "similarity": 0.5  # Default similarity for keyword match
                    })
            
            return relevant_messages[:limit]
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            return []
    
    async def store_user_preference(self, user_id: int, key: str, value: Any):
        """Store user preference in Redis hash"""
        try:
            pref_key = f"user:{user_id}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)
            
            await self.redis_client.hset(pref_key, key, value)
            await self.redis_client.expire(pref_key, 90 * 24 * 3600)  # 90 days TTL
            
        except Exception as e:
            logger.error(f"❌ Failed to store user preference: {e}")
    
    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        """Get user preference from Redis hash"""
        try:
            pref_key = f"user:{user_id}"
            value = await self.redis_client.hget(pref_key, key)
            
            if value is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"❌ Failed to get user preference: {e}")
            return None
    
    async def clear_conversation(self, user_id: int):
        """Clear conversation history for a user"""
        try:
            conversation_key = f"conversation:{user_id}"
            await self.redis_client.delete(conversation_key)
            logger.info(f"✅ Cleared conversation for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear conversation: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            info = await self.redis_client.info()
            
            # Count conversations
            conversation_keys = await self.redis_client.keys("conversation:*")
            message_keys = await self.redis_client.keys("message:*")
            user_keys = await self.redis_client.keys("user:*")
            
            return {
                "redis_memory_used": info.get("used_memory_human", "Unknown"),
                "total_conversations": len(conversation_keys),
                "total_messages": len(message_keys),
                "total_users": len(user_keys),
                "redis_connected": True
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {"redis_connected": False}
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Redis connection closed")

# Fallback in-memory storage for when Redis is unavailable
class InMemoryFallback:
    """Simple in-memory fallback storage"""
    
    def __init__(self):
        self.conversations = {}
        self.user_preferences = {}
        self.messages = {}
    
    async def store_message(self, message: Message):
        """Store message in memory"""
        user_id = message.user_id
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "message_id": message.message_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        })
        
        # Keep only last 50 messages
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history from memory"""
        if user_id not in self.conversations:
            return []
        
        return self.conversations[user_id][-limit:]
    
    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Simple keyword search fallback"""
        history = await self.get_conversation_history(user_id, 50)
        query_lower = query.lower()
        
        results = []
        for msg in history:
            if query_lower in msg["content"].lower():
                results.append({**msg, "similarity": 0.5})
        
        return results[:limit]
    
    async def store_user_preference(self, user_id: int, key: str, value: Any):
        """Store user preference in memory"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id][key] = value
    
    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        """Get user preference from memory"""
        return self.user_preferences.get(user_id, {}).get(key)
    
    async def clear_conversation(self, user_id: int):
        """Clear conversation from memory"""
        if user_id in self.conversations:
            self.conversations[user_id] = []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory stats"""
        return {
            "total_conversations": len(self.conversations),
            "total_messages": sum(len(conv) for conv in self.conversations.values()),
            "total_users": len(self.user_preferences),
            "redis_connected": False,
            "fallback_mode": True
        }

# Database manager with fallback
class DatabaseManager:
    """Main database manager with Redis + fallback"""
    
    def __init__(self, redis_url: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.redis_db = RedisDatabase(redis_url, embedding_model)
        self.fallback = InMemoryFallback()
        self.use_redis = True
    
    async def connect(self):
        """Connect to Redis with fallback"""
        try:
            await self.redis_db.connect()
            self.use_redis = True
            logger.info("✅ Using Redis for storage")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            logger.info("🔄 Using in-memory fallback storage")
            self.use_redis = False
    
    async def store_message(self, message: Message):
        """Store message with fallback"""
        if self.use_redis:
            try:
                await self.redis_db.store_message(message)
                return
            except Exception as e:
                logger.warning(f"⚠️ Redis store failed: {e}, using fallback")
                self.use_redis = False
        
        await self.fallback.store_message(message)
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get conversation history with fallback"""
        if self.use_redis:
            try:
                return await self.redis_db.get_conversation_history(user_id, limit)
            except Exception as e:
                logger.warning(f"⚠️ Redis get failed: {e}, using fallback")
                self.use_redis = False
        
        return await self.fallback.get_conversation_history(user_id, limit)
    
    async def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Semantic search with fallback"""
        if self.use_redis:
            try:
                return await self.redis_db.semantic_search(user_id, query, limit)
            except Exception as e:
                logger.warning(f"⚠️ Redis search failed: {e}, using fallback")
                self.use_redis = False
        
        return await self.fallback.semantic_search(user_id, query, limit)
    
    async def store_user_preference(self, user_id: int, key: str, value: Any):
        """Store user preference with fallback"""
        if self.use_redis:
            try:
                await self.redis_db.store_user_preference(user_id, key, value)
                return
            except Exception as e:
                logger.warning(f"⚠️ Redis preference store failed: {e}, using fallback")
                self.use_redis = False
        
        await self.fallback.store_user_preference(user_id, key, value)
    
    async def get_user_preference(self, user_id: int, key: str) -> Optional[Any]:
        """Get user preference with fallback"""
        if self.use_redis:
            try:
                return await self.redis_db.get_user_preference(user_id, key)
            except Exception as e:
                logger.warning(f"⚠️ Redis preference get failed: {e}, using fallback")
                self.use_redis = False
        
        return await self.fallback.get_user_preference(user_id, key)
    
    async def get_archived_messages(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get archived messages with fallback"""
        if self.use_redis:
            try:
                return await self.redis_db.get_archived_messages(user_id, limit)
            except Exception as e:
                logger.warning(f"⚠️ Redis archive get failed: {e}, using fallback")
                self.use_redis = False
        
        # Fallback: return empty list (in-memory doesn't have archives)
        return []
    
    async def clear_conversation(self, user_id: int):
        """Clear conversation with fallback"""
        if self.use_redis:
            try:
                await self.redis_db.clear_conversation(user_id)
                return
            except Exception as e:
                logger.warning(f"⚠️ Redis clear failed: {e}, using fallback")
                self.use_redis = False
        
        await self.fallback.clear_conversation(user_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get stats with fallback"""
        if self.use_redis:
            try:
                stats = await self.redis_db.get_stats()
                stats["fallback_mode"] = False
                return stats
            except Exception as e:
                logger.warning(f"⚠️ Redis stats failed: {e}, using fallback")
                self.use_redis = False
        
        stats = await self.fallback.get_stats()
        stats["fallback_mode"] = True
        return stats
    
    async def close(self):
        """Close connections"""
        if self.use_redis:
            await self.redis_db.close()
