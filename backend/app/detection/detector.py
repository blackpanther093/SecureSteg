"""
Steganalysis and hidden data detection algorithms.
"""

import numpy as np
import cv2
import struct
from scipy import stats


class SteganalysisDetector:
    """Detects presence of hidden data in media files."""
    
    @staticmethod
    def analyze_lsb_distribution(image: np.ndarray) -> dict:
        """
        Analyze LSB distribution pattern anomalies.
        
        Returns metrics indicating presence of hidden data.
        """
        if len(image.shape) == 3:
            # If color image, flatten to single channel for analysis
            flat_image = image.flatten()
        else:
            flat_image = image.flatten()
        
        # Extract LSBs 
        lsbs = flat_image & 1
        
        # Chi-square test
        ones_count = np.sum(lsbs)
        zeros_count = len(lsbs) - ones_count
        
        # In natural images, distribution should be somewhat random
        expected = len(lsbs) / 2
        chi_square = ((ones_count - expected)**2 + (zeros_count - expected)**2) / expected
        
        # LSB pairs analysis
        lsb_pairs = (flat_image >> 1) & 1
        pair_correlation = np.corrcoef(lsbs[:len(lsbs)-1], lsbs[1:])[0, 1]
        
        return {
            'chi_square_statistic': float(chi_square),
            'lsb_ones_ratio': float(ones_count / len(lsbs)),
            'lsb_entropy': float(stats.entropy([ones_count, zeros_count])),
            'pair_correlation': float(pair_correlation),
            'anomaly_score': float(min(1.0, abs(pair_correlation) * 2))
        }
    
    @staticmethod
    def analyze_color_channels(image: np.ndarray) -> dict:
        """
        Analyze relationships between color channels.
        Hidden data disrupts natural channel correlations.
        """
        if len(image.shape) != 3 or image.shape[2] < 3:
            return {'error': 'Grayscale image', 'correlation': 0}
        
        r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]
        
        r_flat = r.flatten()
        g_flat = g.flatten()
        b_flat = b.flatten()
        
        # Natural images have correlated channels
        rg_corr = np.corrcoef(r_flat, g_flat)[0, 1]
        rb_corr = np.corrcoef(r_flat, b_flat)[0, 1]
        gb_corr = np.corrcoef(g_flat, b_flat)[0, 1]
        
        mean_correlation = np.mean([rg_corr, rb_corr, gb_corr])
        
        return {
            'r_g_correlation': float(rg_corr),
            'r_b_correlation': float(rb_corr),
            'g_b_correlation': float(gb_corr),
            'mean_correlation': float(mean_correlation),
            'correlation_anomaly': float(1.0 - abs(mean_correlation))
        }
    
    @staticmethod
    def analyze_entropy(image: np.ndarray) -> dict:
        """
        Analyze entropy patterns. Encrypted data increases entropy.
        """
        if len(image.shape) == 3:
            flat = image.flatten()
        else:
            flat = image.flatten()
        
        hist, _ = np.histogram(flat, 256, [0, 256])
        hist = hist[hist > 0]
        hist = hist / len(flat)
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        # Peak analysis - embedded data creates more uniform distribution
        max_hist = np.max(hist)
        min_hist = np.min(hist[hist > 0])
        
        return {
            'shannon_entropy': float(entropy),
            'normalized_entropy': float(entropy / 8.0),
            'histogram_max': float(max_hist),
            'histogram_min': float(min_hist),
            'uniformity_score': float(1.0 - (max_hist - min_hist))
        }
    
    @staticmethod
    def detect_hidden_data(image: np.ndarray, sensitivity: str = 'medium') -> dict:
        """
        Overall detection analysis combining multiple metrics.
        
        Args:
            image: Image to analyze
            sensitivity: 'low', 'medium', 'high'
        
        Returns:
            Detection report with probability score
        """
        lsb_analysis = SteganalysisDetector.analyze_lsb_distribution(image)
        channel_analysis = SteganalysisDetector.analyze_color_channels(image)
        entropy_analysis = SteganalysisDetector.analyze_entropy(image)
        
        # Combine scores
        scores = []
        weights = []
        
        # LSB anomaly
        if lsb_analysis['anomaly_score'] > 0.3:
            scores.append(min(1.0, lsb_analysis['anomaly_score']))
            weights.append(0.3)
        
        # Channel correlation anomaly
        if 'correlation_anomaly' in channel_analysis:
            scores.append(channel_analysis['correlation_anomaly'])
            weights.append(0.3)
        
        # Entropy anomaly (encrypted data has high entropy)
        if entropy_analysis['normalized_entropy'] > 0.95:
            scores.append(min(1.0, entropy_analysis['normalized_entropy'] - 0.90))
            weights.append(0.4)
        
        if scores:
            weighted_score = np.average(scores, weights=weights[:len(scores)])
        else:
            weighted_score = 0.0
        
        # Adjust sensitivity
        if sensitivity == 'low':
            threshold = 0.6
        elif sensitivity == 'high':
            threshold = 0.3
        else:
            threshold = 0.45
        
        probability = min(1.0, weighted_score)
        
        detected = bool(probability > threshold)  # Convert numpy.bool_ to Python bool
        
        return {
            'hidden_data_detected': detected,
            'probability': float(probability),
            'confidence': float(min(1.0, probability * 1.5)),
            'sensitivity': sensitivity,
            'lsb_metrics': lsb_analysis,
            'channel_metrics': channel_analysis,
            'entropy_metrics': entropy_analysis,
            'recommendation': "Likely contains hidden data" if detected else "No obvious hidden data detected",
            'detailed_analysis': {
                'lsb_anomaly': float(lsb_analysis.get('anomaly_score', 0)),
                'channel_anomaly': float(channel_analysis.get('correlation_anomaly', 0)),
                'entropy_anomaly': float(max(0, entropy_analysis['normalized_entropy'] - 0.9))
            }
        }
