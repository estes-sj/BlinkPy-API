# BlinkPy API

A lightweight Flask microservice that provides endpoints for interacting with Blink cameras using [blinkpy](https://github.com/fronzbot/blinkpy). List cameras, capture snapshots, and download recent or past clips via simple HTTP requests.

Ideal for automatically storing videos on a local server, offering more explicit control and faster responsiveness with the Blink API compared to Home Assistant integrations.

## Features

* **List Cameras**: Retrieve available Blink camera names and their attributes.
* **Snapshot Capture**: Trigger a snapshot on any camera and get a public URL to the image.
* **Recent Clips**: Download clips since the the specified delta (last 6 hours as default) from the Blink cloud or local Sync Module.
* **Clips Since Timestamp**: Download clips since any provided ISO timestamp from the Blink cloud or local Sync Module.
* **Home Assistant Support**: Utilize endpoints for Home Assistant automations and scripts.
* **Plex**: Organize clips for viewing by media servers like Plex.

## Installation

You can run the Blink API either via **Docker Compose** or in a **Python virtual environment**. Before you begin, clone the repo and create your `.env` file.

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-org/BlinkPy-API.git
   cd BlinkPy-API
   ```

2. **Create and populate your environment file**
   Copy the example and fill in your Blink credentials and any overrides:

   ```bash
   cp env.example .env
   ```

   Edit `.env` and set at minimum:

   ```dotenv
   USERNAME=your_blink_username
   PASSWORD=your_blink_password
   ```
   See [Environment Variables](#environment-variables) for additional optional variables.

### Via Docker Compose

1. **Review `docker-compose.yml`**

   * By default it mounts:

     * `./credentials.json` → `/app/credentials.json`
     * `./media`           → `/app/media`
   * It also loads `./.env` for all other config variables.

2. **Build & start**

   ```bash
   docker compose up -d --build
   ```

3. **Logs & status**

   ```bash
   docker compose logs -f blink-api
   docker compose ps
   ```

### Via Python Virtual Environment

1. **Create & activate venv**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

3. **Run the service**
   The Flask app reads your `.env` automatically (via python-dotenv if installed):

   ```bash
   export FLASK_APP=api.app
   flask run --host 0.0.0.0 --port 5001
   ```

   By default it will be available at [http://0.0.0.0:5001](http://0.0.0.0:5001).


> [!NOTE]
> - If a `credentials.json` file doesn’t exist (or is missing username/password), the app will fall back to `USERNAME`/`PASSWORD` from `.env` and **auto-generate** `credentials.json` on first successful login.
> - To change look-back windows or total-keep limits, tweak `TIMEDELTA_HOURS`, `RECENTS_HOURS`, and `RECENTS_TOTAL` in your `.env`.
> - Make sure your host machine’s timezone matches the `TZ` you set in Docker Compose (default `America/New_York`).

### Environment Variables
Below is a table of all the support environment variables that can be set in the `.env`:

| Variable              | Default Value             | Description                                                                               |
| --------------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| `USERNAME`            | `your_blink_username`     | Your Blink account username (email)                                       |
| `PASSWORD`            | `Suffrage-Siren-Citadel3` | Your Blink account password                                                               |
| `LAST_IMAGE_FILENAME` | `last_snap.jpg`           | Filename to store the most recent snapshot image                                          |
| `TIMEDELTA_HOURS`     | `6`                       | How many past hours to look back for new media (e.g., `6` = last 6 hours). Note that the Blink service appears to only handle 6 hour increments.                 |
| `RECENTS_HOURS`       | `0`                       | If > 0, only include videos within the last X hours; if `0`, uses `RECENTS_TOTAL` instead |
| `RECENTS_TOTAL`       | `20`                      | Max number of videos to keep in the “latest” folder when `RECENTS_HOURS` is `0`           |

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

#### POST `/download-recent-clips`, `/download-recent-clips-and-sort`, and `/download-recent-sync-clips-and-sort`

Download clips from all or specified cameras since the last run.

The `/download-recent-clips-and-sort` and `/download-recent-sync-clips-and-sort` versions sorts by year, month, and date using subholders. Additionally, the `path/to/media/latest` folder is updated with the most recent 20 videos.

The `/download-recent-sync-clips-and-sort` allows downloading from the sync module (when using a free Blink plan).

> [!NOTE]
> Downloading from the sync module tends to have greater latency. According to the BlinkPy docs: "the Blink app has to query the sync module for all information regarding the stored clips. On a click to view a clip, the app asks for the full list of stored clips, finds the clip in question, uploads the clip to the cloud, and then downloads the clip back from a cloud URL. Each interaction requires polling for the response since networking conditions are uncertain. The app also caches recent clips and the manifest."

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

#### POST `/download-clips-since`, `/download-clips-since-and-sort`, and `/download-sync-clips-since-and-sort`

Download clips from all or specified cameras since a given ISO timestamp.

The `/download-clips-since-and-sort` and `/download-sync-clips-since-and-sort` versions sorts by year, month, and date using subholders. Additionally, the `path/to/media/latest` folder is updated with the most recent 20 videos.

The `/download-sync-clips-since-and-sort` allows downloading from the sync module (when using a free Blink plan).

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
