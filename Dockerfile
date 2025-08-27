# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set the working directory
WORKDIR /code

# 3. Set the PYTHONPATH environment variable
# This tells Python to look for modules in the /code directory
ENV PYTHONPATH=/code

# 4. Copy the requirements file
COPY backend/requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy your application code into a 'backend' subfolder
# This preserves the 'from backend...' import structure
COPY ./backend /code/backend

# 7. Expose the port the app runs on
EXPOSE 8080

# 8. Define the command to run your app, updating the path to 'main'
CMD CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$PORT"]