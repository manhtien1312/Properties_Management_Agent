"""
Script to create/update conversation thread tables in the database
"""
from src.database.database import engine, Base
from src.database.models import ConversationThread, ConversationMessage
from sqlalchemy import inspect

def create_conversation_tables():
    """Create or update ConversationThread and ConversationMessage tables"""
    print("Creating/updating conversation tables...")
    
    inspector = inspect(engine)
    
    # Drop existing tables if they exist (for migration)
    if inspector.has_table("ConversationMessage"):
        print("  - Dropping old ConversationMessage table...")
        ConversationMessage.__table__.drop(engine)
    
    if inspector.has_table("ConversationThread"):
        print("  - Dropping old ConversationThread table...")
        ConversationThread.__table__.drop(engine)
    
    # Create tables with new schema
    ConversationThread.__table__.create(engine, checkfirst=True)
    ConversationMessage.__table__.create(engine, checkfirst=True)
    
    print("✅ Conversation tables created successfully!")
    print("   - ConversationThread")
    print("   - ConversationMessage (with context_data column)")

if __name__ == "__main__":
    create_conversation_tables()
