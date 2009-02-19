import os

STARTER_FILE = "%STARTER_FILE%"

def main():
  if os.path.exists(STARTER_FILE):
    os.remove(STARTER_FILE)
    
if __name__ == "__main__":
  main()
