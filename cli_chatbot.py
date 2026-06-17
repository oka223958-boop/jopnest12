import sys
import os
import pandas as pd
import warnings

# Force UTF-8 encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Suppress warnings
warnings.filterwarnings("ignore")

# Add the project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

try:
    from chatbot.engine import ChatbotEngine
    from models.hybrid_engine import HybridRecommendationEngine
    from utils.data_loader import load_dataset, load_jobs, load_users
    from utils.logger import get_logger
except ImportError as e:
    print(f"Import Error: {e}")
    print(r"Make sure you are running this from the project root (d:\jobnest - Copy)")
    sys.exit(1)

log = get_logger(__name__)

def main():
    print("\n" + "="*50)
    print("   JobNest AI Chatbot - Terminal Interface")
    print("="*50)
    
    try:
        log.info("Loading recommendation engine...")
        engine = HybridRecommendationEngine()
        if engine.is_ready():
            engine.load()
        else:
            print("Error: Trained models not found in models/saved/")
            print("Please run 'python train.py' first.")
            return

        log.info("Loading data tables (this might take a few seconds)...")
        # Optimization: We only need jobs and users, loading full dataset for initialization
        df = load_dataset()
        jobs = load_jobs(df)
        users = load_users(df)
        
        # Load courses
        courses = None
        courses_path = os.path.join(PROJECT_ROOT, "data", "jobnest_courses_dataset.csv")
        if os.path.exists(courses_path):
            courses = pd.read_csv(courses_path, encoding="utf-8-sig")
            log.info(f"Loaded {len(courses)} courses.")
        else:
            log.warning("Courses dataset not found at data/jobnest_courses_dataset.csv")
        
        bot = ChatbotEngine(jobs, users, courses, engine)
        
        print("\n" + "*"*50)
        print("Bot is ready! You can start chatting.")
        print("Type 'exit' or 'quit' to close the chatbot.")
        print("*"*50 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ["exit", "quit", "exit()", "quit()"]:
                    print("\nGoodbye! Have a great day.")
                    break
                
                if not user_input:
                    continue
                
                # Get response from chatbot
                response = bot.chat(user_input)
                
                print(f"\nAI: {response['reply']}")
                
                # Show results if any
                if response.get("results"):
                    print(f"\n--- {response['intent'].replace('_', ' ').title()} Results ({response['count']}) ---")
                    # Display top 3 results for brevity
                    for i, item in enumerate(response["results"][:3]):
                        title = item.get("title") or "Unknown Title"
                        # For jobs
                        if "company_name" in item:
                            location = item.get("job_location", "Remote")
                            print(f"{i+1}. {title} at {item['company_name']} ({location})")
                        # For courses
                        elif "platform" in item:
                            print(f"{i+1}. {title} on {item['platform']} (Rating: {item.get('rating', 'N/A')})")
                        else:
                            print(f"{i+1}. {title}")
                            
                    if response["count"] > 3:
                        print(f"... and {response['count'] - 3} more results.")
                    print("-" * 40)
                
                # Show follow up if exists
                if response.get("follow_up"):
                    print(f"Hint: {response['follow_up']}")
                
                print("\n" + "_"*30 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError processing message: {e}")
                
    except Exception as e:
        print(f"\nCritical Initialization Error: {e}")

if __name__ == "__main__":
    main()
