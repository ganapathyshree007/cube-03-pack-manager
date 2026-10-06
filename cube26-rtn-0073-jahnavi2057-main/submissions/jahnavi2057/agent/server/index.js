require('dotenv').config();
const express = require('express');
const cors = require('cors');
const apiRoutes = require('./api');

const path = require('path');

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Serve static images for fixtures
app.use('/fixtures', express.static(path.join(__dirname, 'data/fixtures')));

// API mounting
app.use('/api', apiRoutes);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', time: new Date() });
});

app.listen(port, () => {
  console.log(`Returns Manager API running on port ${port}`);
});
