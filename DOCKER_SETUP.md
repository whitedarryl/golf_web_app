# 🐳 Docker Setup Guide - Golf Tournament App

This guide explains how to run the Golf Tournament App using Docker for maximum portability.

## Why Docker?

- **Portable**: Works on any computer with Docker installed
- **Offline**: No internet needed after initial setup
- **Isolated**: Doesn't interfere with other software on your computer
- **Consistent**: Same environment every time

---

## 📋 Prerequisites

1. **Install Docker Desktop** (one-time setup)
   - Windows: Download from https://www.docker.com/products/docker-desktop
   - Install and restart your computer
   - Docker Desktop should be running (look for whale icon in system tray)

---

## 🚀 Quick Start

### First Time Setup

1. **Copy the entire project folder** to your new computer
2. **Double-click `start.bat`**
3. Wait ~30 seconds for Docker to build and start everything
4. Your browser will automatically open to http://localhost:5001

That's it! The app is now running.

### Daily Use

- **Start the app**: Double-click `start.bat`
- **Stop the app**: Double-click `stop.bat`

---

## 🔧 Configuration

### Environment Variables

Edit the `.env` file to customize database credentials:

```env
DB_HOST=db
DB_USER=golf_user
DB_PASSWORD=golf_password
DB_NAME=golf_scores
DB_ROOT_PASSWORD=rootpassword
SECRET_KEY=your-secret-key-change-this
```

**Important**: After changing `.env`, restart the app:
```bash
docker-compose down
docker-compose up -d
```

---

## 📂 What Gets Saved?

### Persistent Data (survives restarts)
- ✅ **Database**: All scores, players, tournaments
- ✅ **Excel files**: Your scoring sheets
- ✅ **Archives**: Historical tournament data

### Location
All data is stored in Docker volumes which persist between runs.

---

## 🛠️ Useful Commands

### View Logs
```bash
docker-compose logs -f
```

### Restart the App
```bash
docker-compose restart
```

### Stop and Remove Everything (including database)
```bash
docker-compose down -v
```
⚠️ **Warning**: This deletes all data!

### Access MySQL Directly
```bash
docker exec -it golf_mysql mysql -u golf_user -pgolf_password golf_scores
```

---

## 🌐 Accessing the App

Once running, access these URLs:

- **Main Landing Page**: http://localhost:5001
- **Score Calculator**: http://localhost:5001/golf_score_calculator
- **Five Results**: http://localhost:5001/five_results
- **Callaway Results**: http://localhost:5001/callaway_results
- **Historical Data**: http://localhost:5001/historical_data

---

## 📦 Moving to a New Computer

### Step 1: Export Your Data

**Option A - Quick Method (includes everything)**
```bash
# Copy the entire project folder to USB drive or cloud storage
```

**Option B - Backup Database Only**
```bash
docker exec golf_mysql mysqldump -u golf_user -pgolf_password golf_scores > backup.sql
```

### Step 2: On New Computer

1. Install Docker Desktop
2. Copy the project folder
3. Run `start.bat`

If you used Option B (database backup):
```bash
# Start the app first
start.bat

# Then import the backup
docker exec -i golf_mysql mysql -u golf_user -pgolf_password golf_scores < backup.sql
```

---

## 🔒 Offline Usage

The app works **100% offline** after setup:

✅ **No internet required for**:
- Entering scores
- Running calculations
- Viewing results
- Generating leaderboards

❌ **Internet needed only for**:
- Initial Docker Desktop installation
- Downloading the Docker images (first run only)

Once setup is complete, you can use the app anywhere, even without WiFi.

---

## 🐛 Troubleshooting

### Problem: Docker is not running
**Solution**: Start Docker Desktop from your Start menu

### Problem: Port 5001 already in use
**Solution**: Change the port in `docker-compose.yml`:
```yaml
ports:
  - "5002:5001"  # Change first number to any free port
```

### Problem: Can't connect to database
**Solution**: Wait 30 seconds after starting, then check logs:
```bash
docker-compose logs db
```

### Problem: Changes to code not showing up
**Solution**: Rebuild the container:
```bash
docker-compose up -d --build
```

### Problem: Database is empty after restart
**Solution**: Check if volumes exist:
```bash
docker volume ls | findstr golf
```

If missing, your data may have been deleted. Restore from backup.

---

## 🔄 Updating the App

When you get new code updates:

1. Stop the current app: `stop.bat`
2. Replace files with new version
3. Rebuild: `docker-compose up -d --build`

Your database data will be preserved.

---

## 🏗️ Technical Details

### Architecture

```
┌─────────────────────────────────────┐
│  Windows Computer                   │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Docker                       │  │
│  │                               │  │
│  │  ┌────────────┐  ┌─────────┐ │  │
│  │  │ Flask Web  │  │ MySQL   │ │  │
│  │  │ App        │◄─┤ Database│ │  │
│  │  │ Port 5001  │  │ Port    │ │  │
│  │  └────────────┘  │ 3306    │ │  │
│  │                  └─────────┘ │  │
│  └──────────────────────────────┘  │
│         ▲                           │
│         │ http://localhost:5001     │
│         │                           │
│    ┌────┴─────┐                     │
│    │ Browser  │                     │
│    └──────────┘                     │
└─────────────────────────────────────┘
```

### Containers

- **golf_web**: Python Flask application
- **golf_mysql**: MySQL 8.0 database

### Volumes

- **mysql_data**: Persistent database storage

---

## 💡 Tips

1. **Always use `start.bat` and `stop.bat`** - Don't close Docker Desktop directly
2. **Keep backups** of your Excel scoring sheets
3. **Export database regularly** for extra safety
4. **Check Docker Desktop is running** before starting the app

---

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Restart Docker Desktop
3. Try rebuilding: `docker-compose up -d --build`

---

## ✅ Checklist for Tournament Day

- [ ] Docker Desktop is installed and running
- [ ] Project folder is copied to laptop
- [ ] Run `start.bat` before players arrive
- [ ] Test by opening http://localhost:5001
- [ ] Excel scoring sheet is in the project folder
- [ ] Have backup of previous tournament data

---

**You're all set!** 🎉 The app is now portable and can run on any computer with Docker.
