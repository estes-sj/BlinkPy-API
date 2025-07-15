# BlinkPy API

A lightweight Flask microservice that provides endpoints for interacting with Blink cameras using [blinkpy](https://github.com/fronzbot/blinkpy). List cameras, capture snapshots, and download recent or past clips via simple HTTP requests.


## Features

* **List Cameras**: Retrieve available Blink camera names.
* **Snapshot Capture**: Trigger a snapshot on any camera and get a public URL to the image.
* **Recent Clips**: Download clips since the the specified delta (last 6 hours as default).
* **Clips Since Timestamp**: Download clips since any provided ISO timestamp.
* **Home Assistant Support**: Utilize endpoints for Home Assistant automations and scripts.
* **Plex**: Organize clips for viewing by media servers like Plex.

## Installation

Can setup via docker or a virtual environment. But first:

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/BlinkPy-API.git
   cd BlinkPy-API
   ```

2. **Configure environment**

   * Copy `example-credentials.json` to `credentials.json` and fill in your Blink credentials.

   ```json
    {
        "username": "your_blink_account_username",
        "password": "your_blink_account_password"
    }
   ```

### Via Docker Compose

1. **Configure the `docker-compse.yaml`**

   * Adjust any settings such as the path to where you want media stored, the port number used, or the timeszone.

2. **Run via docker**

   ```bash
   docker compose up -d --build
   ```

### Via Virtual Environment

1. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Flask app:

```bash
export FLASK_APP=api.app
flask run --host 0.0.0.0 --port 5001
```

By default the service listens on **[http://0.0.0.0:5001](http://0.0.0.0:5001)**.

### Endpoints

#### GET `/get-camera-info`

Retrieve the list of Blink cameras.

* **Response**

  ```json
  {
      "cameras": [
          {
              "battery": "ok",
              "battery_level": null,
              "battery_voltage": 159,
              "camera_id": "512745",
              "last_record": null,
              "motion_detected": false,
              "motion_enabled": true,
              "name": "Outdoor-Cam",
              "network_id": 422611,
              "recent_clips": [],
              "serial": "SOMESERIAL",
              "sync_module": "Home",
              "sync_signal_strength": null,
              "temperature": 91,
              "temperature_c": 32.8,
              "temperature_calibrated": 91,
              "thumbnail": "https://some-url",
              "type": "catalina",
              "version": "10.70",
              "video": null,
              "wifi_strength": -56
          },
          ...
      ]
  }
  ```

#### POST `/snap`

Trigger a snapshot and get the URL of the saved image.

* **Payload**

  ```json
  { "camera_name": "Front Door" }
  ```

* **Response**

  ```json
  { "url": "https://static.example.com/Front Door/last.jpg" }
  ```

#### POST `/download-recent-clips` and `/download-recent-clips-and-sort`

Download clips from all or specified cameras since the last run. The `/download-recent-clips-and-sort` version sorts by year, month, and date using subholders. Additionally, the `path/to/media/latest` folder is updated with the most recent 20 videos.

* **Payload** (optional)

  ```json
  { "camera_name": "Backyard" }
  ```

* **Response**

  ```json
  {
      "downloaded_clips": {
          "Backyard": [
              "media/Backyard/Backyard-2025-07-01t10-36-54-00-00.mp4"
          ],
          "Living Room": []
      },
      "since": "2025-07-01T08:00:00+00:00"
  }
  ```

#### POST `/download-clips-since`

Download clips from all or specified cameras since a given ISO timestamp. The `/download-clips-since-and-sort` version sorts by year, month, and date using subholders. Additionally, the `path/to/media/latest` folder is updated with the most recent 20 videos.

* **Payload**

  ```json
  {
    "camera_name": ["Front Door","Living Room"],
    "since": "2025-06-30T08:00:00+00:00"
  }
  ```

* **Response**

  ```json
  {
      "downloaded_clips": {
          "Front Door": [
              "media/Front Door/Front Door-2025-07-02t05-36-54-00-00.mp4"
          ],
          "Living Room": []
      },
      "since": "2025-06-30T08:00:00+00:00"
  }
  ```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
