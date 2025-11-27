from typing import Dict, Optional
import hashlib
from datetime import datetime, timedelta


class QueryCache:
    """
    In memory cache for SQL queries.
    Stores question -> SQL mapping with TTL.
    """
    def __init__(self, ttl_hours:int=24):
        self.cache: Dict[str,dict] = {}
        self.ttl = timedelta(hours=ttl_hours)

    
    def _normalize_question(self, question:str):
        """ Normalize the question to create cache key """
        normalized = ''.join(question.lower().strip().split())
        return normalized

    def _get_cache_key(self, question:str):
        """ Get the cache key for question """
        normalized = self._normalize_question(question)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self,question:str):
        """ Get the SQL query for question from cache """
        cache_key = self._get_cache_key(question)

        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]

        # Check if expired
        if datetime.now() - entry['timestamp'] > self.ttl:
            del self.cache[cache_key]
            return
        
        # Update hits and last accessed time
        entry['hits'] += 1
        entry['last_accessed'] = datetime.now()

        return entry['sql']
    
    def set(self, question: str, sql: str):
        """ store sql in cache """
        cache_key = self._get_cache_key(question)

        self.cache[cache_key]={
            "question": question,
            "sql":sql,
            "timestamp":datetime.now(),
            "hits":0,
            "last_accessed":datetime.now()
        }

    def get_stats(self):
        """ Get cache stats """
        total_entries = len(self.cache)
        total_hits = sum(entry['hits'] for entry in self.cache.values())

        # Top queries
        popular = sorted(self.cache.values(), key=lambda x: x['hits'], reverse=True)

        return {
            "total_cached_query": total_entries,
            "total_cache_hits":total_hits,
            "cache_hit_rate": f"{total_hits / max(total_hits + total_entries, 1) * 100:.1f}%",
            "most_popular": [
                {"question": q['question'], "hits": q['hits']}
                for q in popular[:5]
            ]

        }
