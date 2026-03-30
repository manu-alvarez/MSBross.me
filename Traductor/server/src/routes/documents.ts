import { Router } from 'express';
import multer from 'multer';
import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';

const router = Router();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

router.post('/extract-text', upload.single('file'), async (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: 'No se recibió ningún archivo' });

  try {
    let texto = '';

    if (file.mimetype === 'application/pdf' || file.originalname.endsWith('.pdf')) {
      const data = await pdfParse(file.buffer);
      texto = data.text;
    } else if (
      file.mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
      file.originalname.endsWith('.docx')
    ) {
      const result = await mammoth.extractRawText({ buffer: file.buffer });
      texto = result.value;
    } else {
      texto = file.buffer.toString('utf-8');
    }

    return res.json({ texto: texto.trim() });
  } catch (err: any) {
    console.error(err);
    return res.status(500).json({ error: 'Error extrayendo texto', details: err?.message });
  }
});

export default router;
