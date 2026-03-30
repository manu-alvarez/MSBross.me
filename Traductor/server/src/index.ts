import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import processRouter from './routes/process.js';
import documentsRouter from './routes/documents.js';
import extrasRouter from './routes/extras.js';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json({ limit: '2mb' }));

app.use('/api', processRouter);
app.use('/api', documentsRouter);
app.use('/api', extrasRouter);

app.listen(PORT, () => {
  console.log(`API escuchando en http://localhost:${PORT}`);
});
