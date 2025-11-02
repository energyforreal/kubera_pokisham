#!/usr/bin/env python3
"""
Safe Trading Bot Runner

This script provides better signal handling and graceful shutdown
for the trading bot to prevent Ctrl+C hanging issues.
"""

import asyncio
import signal
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class SafeTradingBot:
    """Safe wrapper for the trading bot with proper signal handling."""
    
    def __init__(self):
        self.running = True
        self.agent = None
        self.tasks = []
        self.shutdown_timeout = 30  # 30 seconds for graceful shutdown
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")
        self.running = False
    
    async def run_agent(self):
        """Run the trading agent with proper task management."""
        try:
            # Import here to avoid circular imports
            from src.main import TradingAgent
            
            # Create and initialize agent
            self.agent = TradingAgent()
            await self.agent.initialize()
            
            # Start background tasks
            if hasattr(self.agent, 'trading_loop'):
                task = asyncio.create_task(self.agent.trading_loop())
                self.tasks.append(task)
                logger.info("Started trading loop")
            
            if hasattr(self.agent, 'position_monitoring_loop'):
                task = asyncio.create_task(self.agent.position_monitoring_loop())
                self.tasks.append(task)
                logger.info("Started position monitoring loop")
            
            if hasattr(self.agent, 'data_sync') and hasattr(self.agent.data_sync, 'start_sync'):
                task = asyncio.create_task(self.agent.data_sync.start_sync())
                self.tasks.append(task)
                logger.info("Started data sync service")
            
            # Wait for shutdown signal
            while self.running:
                await asyncio.sleep(1)
            
            logger.info("Shutdown signal received, stopping tasks...")
            
        except Exception as e:
            logger.error(f"Error in trading agent: {e}", exc_info=True)
            self.running = False
    
    async def shutdown(self):
        """Graceful shutdown of all components."""
        logger.info("Starting graceful shutdown...")
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task: {task.get_name()}")
        
        # Wait for tasks to complete with timeout
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout
                )
                logger.info("All tasks completed gracefully")
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown timeout after {self.shutdown_timeout}s, forcing exit")
        
        # Stop agent if it exists
        if self.agent:
            try:
                await asyncio.wait_for(self.agent.stop(), timeout=10)
                logger.info("Trading agent stopped")
            except asyncio.TimeoutError:
                logger.warning("Agent stop timeout, forcing exit")
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")
        
        logger.info("Safe shutdown complete")
    
    async def run(self):
        """Main run method with signal handling."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Run the agent
            await self.run_agent()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            # Always attempt graceful shutdown
            await self.shutdown()


async def main():
    """Main entry point."""
    logger.info("Starting Safe Trading Bot...")
    
    bot = SafeTradingBot()
    await bot.run()
    
    logger.info("Safe Trading Bot ended")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
