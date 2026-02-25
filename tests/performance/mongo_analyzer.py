"""
MongoDB Query Performance Analyzer

Analyzes MongoDB query performance and provides optimization recommendations.
Run with: python tests/performance/mongo_analyzer.py
"""
import sys
import os
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ['RUNMODE'] = 'test'

from apps.wfcatalog_client import get_db_client
from apps.settings import settings


class MongoPerformanceAnalyzer:
    """Analyze MongoDB performance and indexes"""
    
    def __init__(self):
        self.client = get_db_client()
        self.db = self.client.get_database(settings.mongodb_name)
        self.collection = self.db.availability
    
    def check_indexes(self):
        """List all indexes and their usage"""
        print("\n" + "="*60)
        print("MONGODB INDEXES")
        print("="*60 + "\n")
        
        indexes = list(self.collection.list_indexes())
        
        for idx in indexes:
            print(f"Index: {idx['name']}")
            print(f"  Keys: {idx['key']}")
            if 'unique' in idx:
                print(f"  Unique: {idx['unique']}")
            print()
        
        # Get index stats (requires MongoDB 3.2+)
        try:
            stats = list(self.collection.aggregate([{"$indexStats": {}}]))
            print("\nIndex Usage Statistics:")
            print("-" * 60)
            for stat in stats:
                print(f"\nIndex: {stat['name']}")
                print(f"  Accesses: {stat['accesses']['ops']}")
                print(f"  Since: {stat['accesses']['since']}")
        except Exception as e:
            print(f"⚠️  Index stats not available: {e}")
    
    def analyze_query(self, query, projection=None):
        """
        Analyze a specific query with explain plan
        
        Args:
            query: MongoDB query dict
            projection: Optional projection dict
        """
        print("\n" + "="*60)
        print("QUERY ANALYSIS")
        print("="*60 + "\n")
        
        print(f"Query: {json.dumps(query, indent=2, default=str)}")
        if projection:
            print(f"Projection: {json.dumps(projection, indent=2)}")
        
        # Get explain plan
        explain = self.collection.find(query, projection).explain()
        
        print("\n" + "-"*60)
        print("Execution Stats:")
        print("-"*60)
        
        exec_stats = explain.get('executionStats', {})
        
        print(f"Execution Time: {exec_stats.get('executionTimeMillis', 'N/A')} ms")
        print(f"Total Docs Examined: {exec_stats.get('totalDocsExamined', 'N/A')}")
        print(f"Total Keys Examined: {exec_stats.get('totalKeysExamined', 'N/A')}")
        print(f"Documents Returned: {exec_stats.get('nReturned', 'N/A')}")
        
        # Check if index was used
        winning_plan = explain.get('queryPlanner', {}).get('winningPlan', {})
        stage = winning_plan.get('stage', 'UNKNOWN')
        
        print(f"\nQuery Stage: {stage}")
        
        if stage == 'COLLSCAN':
            print("⚠️  WARNING: Collection scan detected! Consider adding an index.")
        elif stage == 'IXSCAN' or 'IXSCAN' in str(winning_plan):
            print("✅ Index scan used")
            if 'inputStage' in winning_plan:
                index_name = winning_plan['inputStage'].get('indexName', 'unknown')
                print(f"   Index: {index_name}")
        
        # Calculate efficiency
        docs_examined = exec_stats.get('totalDocsExamined', 0)
        docs_returned = exec_stats.get('nReturned', 0)
        
        if docs_examined > 0:
            efficiency = (docs_returned / docs_examined) * 100
            print(f"\nQuery Efficiency: {efficiency:.2f}%")
            
            if efficiency < 50:
                print("⚠️  Low efficiency - query examines many documents")
    
    def test_common_queries(self):
        """Test common query patterns"""
        print("\n" + "="*60)
        print("TESTING COMMON QUERY PATTERNS")
        print("="*60)
        
        # Query 1: Network + Time range
        print("\n1. Network + Time Range Query")
        self.analyze_query(
            {
                "net": {"$in": ["NL"]},
                "ts": {"$lt": datetime(2023, 2, 1)},
                "te": {"$gt": datetime(2023, 1, 1)}
            },
            projection={"_id": 0, "net": 1, "sta": 1, "ts": 1, "te": 1}
        )
        
        # Query 2: Full NSLC query
        print("\n2. Full NSLC Query")
        self.analyze_query(
            {
                "net": {"$in": ["NL"]},
                "sta": {"$in": ["HGN"]},
                "loc": {"$in": [""]},
                "cha": {"$in": ["BHZ"]},
                "ts": {"$lt": datetime(2023, 2, 1)},
                "te": {"$gt": datetime(2023, 1, 1)}
            }
        )
        
        # Query 3: Quality filter
        print("\n3. Quality Filter Query")
        self.analyze_query(
            {
                "net": {"$in": ["NL"]},
                "qlt": {"$in": ["D"]},
                "ts": {"$lt": datetime(2023, 2, 1)},
                "te": {"$gt": datetime(2023, 1, 1)}
            }
        )
    
    def get_collection_stats(self):
        """Get collection statistics"""
        print("\n" + "="*60)
        print("COLLECTION STATISTICS")
        print("="*60 + "\n")
        
        stats = self.db.command("collStats", "availability")
        
        print(f"Document Count: {stats.get('count', 'N/A'):,}")
        print(f"Average Document Size: {stats.get('avgObjSize', 0):,} bytes")
        print(f"Total Size: {stats.get('size', 0) / 1024 / 1024:.2f} MB")
        print(f"Storage Size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        print(f"Total Index Size: {stats.get('totalIndexSize', 0) / 1024 / 1024:.2f} MB")
        
        # Index sizes
        if 'indexSizes' in stats:
            print("\nIndex Sizes:")
            for idx_name, size in stats['indexSizes'].items():
                print(f"  {idx_name}: {size / 1024 / 1024:.2f} MB")
    
    def recommend_indexes(self):
        """Provide index recommendations"""
        print("\n" + "="*60)
        print("INDEX RECOMMENDATIONS")
        print("="*60 + "\n")
        
        recommendations = [
            {
                "name": "Compound NSLC + Time Index",
                "command": "db.availability.createIndex({ net: 1, sta: 1, loc: 1, cha: 1, ts: 1, te: 1 })",
                "reason": "Optimizes most common query pattern (NSLC + time range)"
            },
            {
                "name": "Time Range Index",
                "command": "db.availability.createIndex({ ts: 1, te: 1 })",
                "reason": "Speeds up time-based queries without NSLC filters"
            },
            {
                "name": "Quality + Time Index",
                "command": "db.availability.createIndex({ qlt: 1, ts: 1, te: 1 })",
                "reason": "Optimizes quality-filtered queries"
            },
            {
                "name": "Network + Time Index",
                "command": "db.availability.createIndex({ net: 1, ts: 1, te: 1 })",
                "reason": "Optimizes network-level queries"
            }
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['name']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Command: {rec['command']}")
            print()


def main():
    """Run MongoDB performance analysis"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       MONGODB PERFORMANCE ANALYZER                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        analyzer = MongoPerformanceAnalyzer()
        
        # Run all analyses
        analyzer.get_collection_stats()
        analyzer.check_indexes()
        analyzer.test_common_queries()
        analyzer.recommend_indexes()
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║                  ANALYSIS COMPLETE                           ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. MongoDB is running")
        print("  2. config.py is configured correctly")
        print("  3. You have access to the database")


if __name__ == '__main__':
    main()
