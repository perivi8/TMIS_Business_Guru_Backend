@echo off
echo 🚀 Deploying Minimal TMIS Backend to Render
echo ==========================================

echo.
echo ✅ Current configuration:
echo    - Using minimal_app.py (lightweight version)
echo    - Includes mock endpoints for /api/clients and /api/enquiries
echo    - Same CORS settings as full app
echo    - No database dependencies for startup

echo.
echo 📦 Adding files to git...
git add .

echo.
echo 💾 Committing changes...
git commit -m "Deploy minimal app with mock endpoints for testing"

echo.
echo 🚀 Pushing to trigger Render deployment...
git push

echo.
echo ⏳ Deployment initiated! 
echo.
echo 🔍 Check deployment status at:
echo    https://dashboard.render.com
echo.
echo 🌐 Once deployed, test these URLs:
echo    https://tmis-business-guru-backend.onrender.com/
echo    https://tmis-business-guru-backend.onrender.com/api/health
echo    https://tmis-business-guru-backend.onrender.com/api/test
echo.
echo 📱 Frontend should now work with mock data!
echo.
pause
