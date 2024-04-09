import os
import subprocess
import base64
import pyperclip

def main():
    # 1. Delete the `token.pickle` file
    token_file = 'token.pickle'
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"Deleted {token_file}")

    # 2. Run `python -m src.email_fetcher`
    print("Starting the email fetcher script. Follow the prompts to authorize.")
    subprocess.run(['python', '-m', 'src.email_fetcher'])

    # 3. Base 64 encode the newly created `token.pickle` file, and copy that value to the clipboard
    if os.path.exists(token_file):
        with open(token_file, 'rb') as file:
            encoded_token = base64.b64encode(file.read()).decode('utf-8')
        pyperclip.copy(encoded_token)
        print(f"The content of {token_file} has been base64 encoded and copied to the clipboard.")
    else:
        print(f"{token_file} not found. Ensure the email fetcher script created the file successfully.")

if __name__ == '__main__':
    main()
