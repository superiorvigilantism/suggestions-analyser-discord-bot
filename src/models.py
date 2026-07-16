from sqlalchemy import Column, BigInteger, Integer, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ServerData(Base):
    __tablename__ = "server_data"
    
    guild_id = Column(BigInteger, primary_key=True)
    threshold = Column(Float, default=6.0)
    prompt = Column(String,
                    default="You are a game suggestions evaluator. "
                            "Rate every suggestion you are presented with by following format:"
                            "\nScore: X/10"
                            "\nReasoning: Lorem Ipsum dolor sit amet...")
    forward_channel_id = Column(BigInteger, default=-1)
    forum_channel_id = Column(BigInteger, default=-1)
    
    def __repr__(self):
        response = (f"<ServerData(guild_id={self.guild_id}, "
                    f"threshold={self.threshold}, "
                    f"prompt={self.prompt}, "
                    f"forward_channel_id={self.forward_channel_id}, "
                    f"forum_channel_id={self.forum_channel_id})>")
        return response
