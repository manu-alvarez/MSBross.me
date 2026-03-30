import { Router } from 'express';
import OpenAI from 'openai';

const router = Router();

const openai = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1',
});

const prompts: Record<string, string> = {
  keywords: 'Eres un experto analista SEO y de contenido. Tu tarea es extraer de 5 a 10 palabras clave o etiquetas (keywords) principales del texto proporcionado. Devuélvelas en una lista con viñetas separada por comas, sin explicaciones adicionales.',
  sentiment: 'Eres un experto en psicología y análisis de lenguaje. Tu tarea es analizar el sentimiento general (positivo, negativo, neutral) y el tono (ej: formal, sarcástico, entusiasta, urgente) del texto proporcionado. Devuelve un breve párrafo o viñetas explicando el sentimiento y el tono, sin explicaciones adicionales.',
  entities: 'Eres un experto en extracción de información (NER). Tu tarea es listar todas las Entidades Nombradas importantes que encuentres en el texto, categorizándolas en: Personas, Organizaciones, Lugares, y Fechas clave. Devuelve la lista jerárquica clara, omitiendo las categorías que no existan en el texto.',
  appbuilder: 'Eres un prestigioso Full-Stack Developer experto en crear prototipos rápidos y PWA. Tu tarea es generar el CÓDIGO de una aplicación o herramienta funcional basada en la descripción que el usuario te dará. Si el usuario pide una web, genera un archivo ÚNICO de HTML que incluya CSS (vibrante y moderno) y JS (lógica funcional). Si pide algo complejo, explica la estructura necesaria. Enfócate en código listo para copiar y usar.',
};

router.post('/extras', async (req, res) => {
  try {
    const { texto, herramienta } = req.body;

    if (!texto || !texto.trim()) {
      return res.status(400).json({ error: 'Texto vacío' });
    }

    const system = prompts[herramienta];
    if (!system) {
      return res.status(400).json({ error: 'Herramienta no válida' });
    }

    const completion = await openai.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      temperature: 0.3,
      messages: [
        { role: 'system', content: system },
        {
          role: 'user',
          content: texto,
        },
      ],
    });

    const content = completion.choices[0]?.message?.content || '';

    return res.json({
      resultado: content.trim(),
    });
  } catch (err: any) {
    console.error(err);
    return res.status(500).json({
      error: 'Error procesando la herramienta extra',
      details: err?.message,
    });
  }
});

export default router;
