# Use an official Python runtime as a base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y ssh
# ...
COPY ./.ssh /root/.ssh
RUN chmod 700 /root/.ssh && chmod 644 /root/.ssh/* && chmod 600 /root/.ssh/id_rsa

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy all the files to the container's working directory
COPY . .

# Run the bot.py script when the container launches
CMD ["python", "bot.py"]