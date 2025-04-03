import ollama

def generate_schedule(user_events: list, free_time: list):
    """
    Calls Llama 3 via Ollama to generate an optimal schedule.
    """
    prompt = f"""
Create a **structured weekly schedule** based on the following constraints:
- **User Events**: {user_events}
- **Free Time Slots**: {free_time}
### Requirements:
1. **Format**:  
   Each event must follow this exact pattern: 
   • <DAY>
   • <START_TIME>-<END_TIME>: <EVENT_NAME>

2. **Rules**:  
   - Prioritize important tasks first.  
   - Allocate time for breaks/meals.  
   - Spread events evenly across the week.  
   - Use **12-hour format** with AM/PM (e.g., `09:00 AM` instead of `09:00`).  

3. **Output**:  
   - Return **ONLY** the schedule in bullet points 
   - Do not include any additional text, explanations, or headers.
   - Ensure correct indentation and formatting.
    **Do not use code blocks or markdown formatting**.
"""

    # Send the query to the model
    response = ollama.generate(
        model="llama3.2:1b",
        prompt=prompt,
        options={
            'temperature': 0.7,
            'num_predict': 500
        }
    )
    

    # Fix: Return the response as a dictionary
    return {"schedule": response['response']}


