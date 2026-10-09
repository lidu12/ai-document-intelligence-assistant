const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const parentDir = path.resolve(__dirname, '..');
console.log('[Shim] Running build in parent frontend directory:', parentDir);

// Run npm install in real frontend directory
execSync('npm install', { cwd: parentDir, stdio: 'inherit' });

// Run npm run build in real frontend directory
execSync('npm run build', { cwd: parentDir, stdio: 'inherit' });

// Copy out directory to this shim directory as well so publish path resolves anywhere
const srcOut = path.join(parentDir, 'out');
const destOut = path.join(__dirname, 'out');

if (fs.existsSync(srcOut)) {
  fs.cpSync(srcOut, destOut, { recursive: true });
  console.log('[Shim] Successfully synced static export files to both locations.');
}
