"""LSTM with Attention Mechanism for time series prediction."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class Attention(nn.Module):
    """Attention mechanism for LSTM."""
    
    def __init__(self, hidden_dim: int):
        super(Attention, self).__init__()
        self.attention = nn.Linear(hidden_dim, 1)
    
    def forward(self, lstm_output):
        """
        Args:
            lstm_output: (batch_size, sequence_length, hidden_dim)
        
        Returns:
            context: (batch_size, hidden_dim)
            attention_weights: (batch_size, sequence_length)
        """
        # Calculate attention scores
        attention_scores = self.attention(lstm_output)  # (batch, seq, 1)
        attention_weights = F.softmax(attention_scores.squeeze(-1), dim=1)  # (batch, seq)
        
        # Apply attention weights
        context = torch.bmm(
            attention_weights.unsqueeze(1),  # (batch, 1, seq)
            lstm_output  # (batch, seq, hidden)
        ).squeeze(1)  # (batch, hidden)
        
        return context, attention_weights


class LSTMAttentionModel(nn.Module):
    """LSTM with Attention for trading signal prediction."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        num_classes: int = 3
    ):
        super(LSTMAttentionModel, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_classes = num_classes
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=False
        )
        
        # Attention mechanism
        self.attention = Attention(hidden_dim)
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_dim, 64)
        self.dropout1 = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, 32)
        self.dropout2 = nn.Dropout(dropout)
        self.fc3 = nn.Linear(32, num_classes)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(32)
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch_size, sequence_length, input_dim)
        
        Returns:
            output: Class predictions (batch_size, num_classes)
            attention_weights: Attention weights (batch_size, sequence_length)
        """
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(x)  # (batch, seq, hidden)
        
        # Attention
        context, attention_weights = self.attention(lstm_out)
        
        # Fully connected layers with batch norm
        x = F.relu(self.bn1(self.fc1(context)))
        x = self.dropout1(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        output = self.fc3(x)
        
        return output, attention_weights


class TradingDataset(Dataset):
    """Dataset for time series trading data."""
    
    def __init__(self, features: np.ndarray, labels: np.ndarray, sequence_length: int = 60):
        """
        Args:
            features: Feature array (samples, features)
            labels: Label array (samples,)
            sequence_length: Number of timesteps in each sequence
        """
        self.features = features
        self.labels = labels
        self.sequence_length = sequence_length
    
    def __len__(self):
        return len(self.features) - self.sequence_length
    
    def __getitem__(self, idx):
        # Get sequence of features
        x = self.features[idx:idx + self.sequence_length]
        # Get corresponding label (predict next step)
        y = self.labels[idx + self.sequence_length]
        
        return torch.FloatTensor(x), torch.LongTensor([y]).squeeze()


class LSTMAttentionTrader:
    """Wrapper class for training and inference."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
        sequence_length: int = 60,
        device: str = 'cpu'
    ):
        self.device = device
        self.sequence_length = sequence_length
        self.input_dim = input_dim
        
        # Initialize model
        self.model = LSTMAttentionModel(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            num_classes=3  # BUY, HOLD, SELL
        ).to(device)
        
        logger.info(
            "LSTM Attention model initialized",
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            device=device
        )
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ):
        """Train the model."""
        # Create datasets
        train_dataset = TradingDataset(X_train, y_train, self.sequence_length)
        val_dataset = TradingDataset(X_val, y_val, self.sequence_length)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-5)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', patience=5, factor=0.5
        )
        
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        logger.info(f"Starting training for {epochs} epochs")
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs, _ = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += batch_y.size(0)
                train_correct += (predicted == batch_y).sum().item()
            
            # Validation
            self.model.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    outputs, _ = self.model(batch_x)
                    loss = criterion(outputs, batch_y)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += batch_y.size(0)
                    val_correct += (predicted == batch_y).sum().item()
            
            # Calculate averages
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            train_acc = 100 * train_correct / train_total
            val_acc = 100 * val_correct / val_total
            
            # Learning rate scheduling
            scheduler.step(avg_val_loss)
            
            # Early stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                # Save best model
                self.save('models/lstm_attention_best.pth')
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
            
            # Log progress
            if (epoch + 1) % 5 == 0:
                logger.info(
                    f"Epoch [{epoch+1}/{epochs}]",
                    train_loss=f"{avg_train_loss:.4f}",
                    val_loss=f"{avg_val_loss:.4f}",
                    train_acc=f"{train_acc:.2f}%",
                    val_acc=f"{val_acc:.2f}%"
                )
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions.
        
        Args:
            X: Feature array (samples, features)
        
        Returns:
            predictions: Class predictions (samples,)
            confidences: Prediction confidences (samples,)
        """
        self.model.eval()
        
        # Create dataset
        dataset = TradingDataset(X, np.zeros(len(X)), self.sequence_length)
        loader = DataLoader(dataset, batch_size=32)
        
        all_predictions = []
        all_confidences = []
        
        with torch.no_grad():
            for batch_x, _ in loader:
                batch_x = batch_x.to(self.device)
                outputs, _ = self.model(batch_x)
                
                # Get probabilities
                probs = F.softmax(outputs, dim=1)
                confidences, predicted = torch.max(probs, 1)
                
                all_predictions.extend(predicted.cpu().numpy())
                all_confidences.extend(confidences.cpu().numpy())
        
        return np.array(all_predictions), np.array(all_confidences)
    
    def save(self, path: str):
        """Save model."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'input_dim': self.input_dim,
            'sequence_length': self.sequence_length
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.input_dim = checkpoint['input_dim']
        self.sequence_length = checkpoint['sequence_length']
        logger.info(f"Model loaded from {path}")


