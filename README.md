# Cognate Explorer - Beta v1.0

**Algorithmic/AI-assisted database** for exploring cognates across Romance languages.

## 🎯 Mission

This project provides a **large-scale cognate dictionary** generated via algorithmic matching across multiple Romance languages. Because it is AI-assisted, some false friends may exist. We invite the community to help prune and improve the list.

## 📊 Dataset

- **37,677 cognates** across 8 languages
- **Algorithmic matching** with similarity scoring
- **Pattern detection** for linguistic relationships
- **Community-driven** improvement process

## 🌍 Languages Covered

- Spanish (es)
- French (fr) 
- Italian (it)
- Portuguese (pt)
- Catalan (ca)
- Galician (gl)
- Romanian (ro)
- English (en)

## 🚀 Features

- **Search**: Language-global cognate discovery
- **Comparative Matrix**: Multi-language grid analysis
- **Random Discovery**: Explore cognate relationships
- **API**: RESTful endpoints for integration

## 📡 API Endpoints

```
GET  /search?q={query}           # Search cognates
GET  /random?count=5             # Random cognate groups
POST /matrix                     # Comparative matrix
GET  /health                     # API status
```

## 🛠️ Tech Stack

- **Backend**: FastAPI + Pandas
- **Frontend**: HTML + Tailwind CSS
- **Deployment**: Render.com
- **Data**: Algorithmic matching with similarity scoring

## 🔬 AI & Algorithmic Approach

Our AI-assisted approach:
1. **Pattern Recognition**: Linguistic similarity algorithms
2. **Similarity Scoring**: Automated confidence metrics
3. **Cross-validation**: Multi-language verification
4. **Community Pruning**: User feedback integration

## 🤝 How to Contribute

Found a false friend? Help us improve:

1. **Report Issues**: Use GitHub Issues with details
2. **Submit PRs**: Direct data corrections and improvements
3. **Linguistic Sources**: Provide etymological references
4. **Language Expertise**: Native speaker validation welcome

### Contribution Guidelines

- Report false cognates with linguistic evidence
- Provide etymological sources for corrections
- Include language codes and IPA where possible
- Follow existing data format
- Help improve algorithmic accuracy

## 📄 License

MIT License - Open source for etymological research.

## ⚠️ Beta Notice

This is **Beta v1.0**. Because it is AI-assisted, some data may still need refinement. Found errors? Please contribute!

---

**Built for linguistic researchers, language learners, and etymology enthusiasts.**
