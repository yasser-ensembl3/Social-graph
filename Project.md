# Social Graph Analysis

A Python-based project for analyzing and visualizing social network graphs. This toolkit provides methods for collecting, processing, and analyzing social network data to uncover patterns, influential nodes, and community structures.

## Overview

This project enables comprehensive social network analysis through graph-based approaches. It supports data collection, network construction, and various analytical methods to understand social dynamics and relationships within networks.

## Features

- **Data Collection**: Gather social network data from various sources via APIs
- **Graph Construction**: Build network graphs representing social relationships
- **Network Analysis**: Compute key metrics such as centrality, clustering coefficients, and path lengths
- **Community Detection**: Identify and analyze communities within the network
- **Visualization**: Generate clear visualizations of network structures and patterns
- **Influence Analysis**: Identify influential nodes using PageRank, HITS, and other algorithms

## Project Structure

```
Social-graph/
├── data/               # Data storage directory
│   ├── raw/           # Raw collected data
│   └── processed/     # Processed network data
├── scripts/           # Analysis and processing scripts
│   ├── collect.py     # Data collection scripts
│   ├── analyze.py     # Network analysis scripts
│   └── visualize.py   # Visualization scripts
├── .env.example       # Environment variables template
├── .gitignore        # Git ignore rules
└── requirements.txt   # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yasser-ensembl3/Social-graph.git
cd Social-graph
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

Create a `.env` file based on `.env.example` and configure the following:

```env
# API Keys
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Data Collection Settings
MAX_NODES=1000
MAX_DEPTH=2

# Analysis Parameters
MIN_COMMUNITY_SIZE=5
```

## Usage

### Data Collection

Collect social network data from your chosen source:

```bash
python scripts/collect.py --source [SOURCE] --output data/raw/network_data.json
```

### Network Analysis

Analyze the collected network data:

```bash
python scripts/analyze.py --input data/raw/network_data.json --output data/processed/analysis_results.json
```

### Visualization

Generate network visualizations:

```bash
python scripts/visualize.py --input data/processed/analysis_results.json --output visualizations/
```

## Key Metrics Analyzed

- **Degree Centrality**: Measures the number of connections each node has
- **Betweenness Centrality**: Identifies nodes that act as bridges between communities
- **Closeness Centrality**: Measures how close a node is to all other nodes
- **Clustering Coefficient**: Quantifies the degree to which nodes cluster together
- **PageRank**: Ranks nodes based on their importance in the network
- **Community Structure**: Detects groups of densely connected nodes

## Dependencies

Main libraries used in this project:

- `networkx` - Network analysis and graph algorithms
- `pandas` - Data manipulation and analysis
- `matplotlib` / `seaborn` - Data visualization
- `numpy` - Numerical computing
- `requests` - HTTP library for API calls
- `python-dotenv` - Environment variable management

See `requirements.txt` for complete list of dependencies.

## Example Workflow

1. **Collect Data**: Gather social network data from your target platform
2. **Build Graph**: Construct a network graph from the collected data
3. **Compute Metrics**: Calculate centrality measures and other network statistics
4. **Detect Communities**: Identify clusters and communities within the network
5. **Visualize Results**: Create plots and diagrams to illustrate findings
6. **Analyze Patterns**: Interpret results to understand social dynamics

## Output Examples

The analysis generates various outputs including:

- Network statistics reports (JSON/CSV)
- Centrality rankings
- Community detection results
- Network visualizations (PNG/PDF)
- Interactive network graphs (HTML)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Best Practices

- Keep API keys secure and never commit them to the repository
- Respect API rate limits when collecting data
- Document any new features or analysis methods
- Follow PEP 8 style guidelines for Python code
- Add appropriate error handling for data collection scripts

## Troubleshooting

### Common Issues

**API Rate Limiting**: If you encounter rate limit errors, adjust the delay between requests or reduce the data collection scope.

**Memory Issues**: For large networks, consider processing data in batches or using more efficient data structures.

**Missing Dependencies**: Ensure all packages in `requirements.txt` are installed correctly.

## Future Enhancements

- Support for additional social platforms
- Real-time network monitoring
- Advanced machine learning-based predictions
- Interactive web dashboard
- Temporal network analysis
- Sentiment analysis integration

## License

This project is open source and available for educational and research purposes.

## Contact

For questions, suggestions, or collaboration opportunities, please open an issue on GitHub.

## Acknowledgments

- NetworkX community for excellent graph analysis tools
- Contributors to the various data collection APIs
- Research community for social network analysis methodologies

---

**Note**: This is a research and educational project. Please ensure you comply with the terms of service of any platforms from which you collect data.