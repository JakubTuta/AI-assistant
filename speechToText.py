from Employer import Employer
from Recognizer import Recognizer

try:
    raw_text = str(Recognizer.recognize_speech_from_mic())

    categorized_command = Recognizer.categorize_command(raw_text)

    print(f"Command: {categorized_command}")

    Employer.job_on_command(categorized_command)

except Exception as e:
    print(f"Error: {e}")
