# MSBross.me - Professional AI-Powered Web Ecosystem

A comprehensive, production-ready web platform featuring multiple AI-integrated applications built with modern technologies. This repository showcases enterprise-level development practices, security hardening, and scalable architecture.

## 🌟 Overview

MSBross.me is a multi-application ecosystem that demonstrates advanced web development techniques, including:

- **Secure API Gateway** with environment-based configuration
- **AI-Powered Applications** using multiple LLM providers (OpenAI, Groq, Gemini, Anthropic)
- **Real-time Voice Assistant** with LiveKit integration
- **Logistics Intelligence Platform** with web search and pricing APIs
- **Restaurant Management System** with FastAPI backend
- **Task Management Suite** with modern React interfaces
- **Document Translation Service** with OCR capabilities

## 🏗️ Architecture

### Core Components
- **API Gateway** (`api.php`): Centralized PHP-based API with provider routing
- **Deployment Automation** (`vps_mirror_deploy.py`): Secure FTP deployment with environment variables
- **Frontend Hub** (`index.html`): Unified access point for all applications

### Applications

#### 🤖 IAPutaOS
AI-powered restaurant ordering system with neural interface.
- **Backend**: Python/FastAPI with Groq LLM integration
- **Frontend**: React with 3D neural orb visualization
- **Features**: Tool dispatch, memory management, multi-provider AI

#### 📦 LogiSearch
Logistics intelligence platform for freight pricing and customs.
- **Tech**: React + Material-UI + Supabase
- **APIs**: Tavily web search, real-time pricing calculations
- **Features**: Multi-modal transport pricing, customs requirements

#### 🎤 Nikolina (LiveKit)
Real-time voice assistant with advanced AI conversation.
- **Tech**: LiveKit for WebRTC, Gemini 2.0 Flash for native audio
- **Features**: Zero-latency voice interaction, multi-model support

#### 🍽️ DOHLER
Restaurant management system with reservation handling.
- **Backend**: FastAPI + SQLite
- **Frontend**: React + Tailwind CSS
- **Features**: Table management, reservation system

#### ✅ TaskFlow Pro
Professional task management with modern UI.
- **Tech**: React + Tailwind + Vite
- **Features**: Project organization, deadline tracking

#### 🌐 Traductor
Document translation service with OCR.
- **Backend**: Node.js/TypeScript
- **Frontend**: React PWA
- **Features**: Multi-format document processing, offline capability

## 🔒 Security Features

- **Environment-Based Configuration**: All secrets managed via `.env` files
- **CORS Hardening**: Strict origin validation
- **Input Validation**: Comprehensive action and payload checking
- **Build Security**: No secrets in compiled assets
- **API Rate Limiting**: Ready for implementation
- **HTTPS Enforcement**: Security headers and HSTS

## 🚀 Deployment

### Prerequisites
- PHP 8.0+
- Python 3.8+
- Node.js 18+
- FTP access to hosting provider

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/manu-alvarez/MSBross.me.git
   cd MSBross.me
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and deployment credentials
   ```

3. **Deploy to production**
   ```bash
   python vps_mirror_deploy.py
   ```

### Environment Variables

See `.env.example` for required configuration:
- API keys for OpenAI, Groq, Gemini, Anthropic
- FTP deployment credentials
- Database connections
- LiveKit server URLs

## 🛠️ Development

### Building Applications

Each sub-application can be built independently:

```bash
# IAPutaOS
cd IAPutaOS && docker-compose up

# LogiSearch
cd LogiSearch && npm install && npm run build

# Nikolina
cd livekit-frontend && npm install && npm run build

# DOHLER
cd dohler_src/frontend && npm install && npm run build

# TaskFlow Pro
cd taskflow_pro_src && npm install && npm run build

# Traductor
cd Traductor/client && npm install && npm run build
```

### API Testing

```bash
# Test API gateway
./test_api.sh

# Comprehensive testing
./test_api_comprehensive.sh
```

## 📊 Project Structure

```
MSBross.me/
├── api.php                    # Main API gateway
├── vps_mirror_deploy.py       # Deployment script
├── index.html                 # Frontend hub
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── PROJECT_SPEC.md           # Project specifications
├── IAPutaOS/                 # AI Restaurant System
├── LogiSearch/               # Logistics Platform
├── livekit-backend/          # Voice Assistant Backend
├── livekit-frontend/         # Voice Assistant Frontend
├── dohler/                   # Restaurant Management (legacy)
├── dohler_src/               # Restaurant Management (modern)
├── taskflow_pro_src/         # Task Management
├── Traductor/                # Translation Service
└── web_dist/                 # Production builds
```

## 🎯 Key Features

- **Multi-Provider AI Integration**: Seamless switching between LLM providers
- **Real-time Capabilities**: WebRTC voice, live updates
- **Progressive Web Apps**: Offline functionality, installable
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Database Integration**: SQLite, Supabase, custom backends
- **Docker Support**: Containerized deployments
- **CI/CD Ready**: GitHub Actions workflows included

## 📈 Performance & Scalability

- **Optimized Builds**: Vite-based bundling with code splitting
- **Lazy Loading**: Component and route-based loading
- **Caching Strategies**: Service workers, HTTP caching
- **CDN Ready**: Static asset optimization
- **Monitoring**: Error tracking and logging infrastructure

## 🤝 Contributing

This repository demonstrates professional development practices:

- **Clean Code**: Well-structured, documented codebase
- **Security First**: No hardcoded secrets, secure practices
- **Modular Architecture**: Independent, maintainable components
- **Testing**: Comprehensive test suites
- **Documentation**: Detailed READMEs and inline comments

## 📄 License

This project is a professional portfolio piece showcasing advanced web development capabilities. All code is original and demonstrates industry best practices.

## 📞 Contact

For deployment inquiries or collaboration opportunities, the codebase serves as a comprehensive demonstration of full-stack development expertise.

---

*Built with ❤️ using modern web technologies - A showcase of professional development excellence*</content>
<filePath="README.md