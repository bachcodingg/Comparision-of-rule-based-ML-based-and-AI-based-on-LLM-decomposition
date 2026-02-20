#!/usr/bin/env python3
"""
Data Collector Module

Handles cloning repositories and preparing data for analysis.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects Java repositories for analysis.
    
    Handles:
    - Cloning Git repositories
    - Organizing repository data
    - Running RefactoringMiner for ground truth
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.raw_dir = Path(config["data"]["raw_dir"])
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        self.repositories = config["data"]["repositories"]
    
    def clone_repositories(self) -> List[Path]:
        """
        Clone all configured repositories.
        
        Returns:
            List of paths to cloned repositories
        """
        cloned_paths = []
        
        for repo in self.repositories:
            repo_name = repo["name"]
            repo_url = repo["url"]
            branch = repo.get("branch", "master")
            
            repo_path = self.raw_dir / repo_name
            
            if repo_path.exists():
                logger.info(f"Repository already exists: {repo_name}")
                cloned_paths.append(repo_path)
                continue
            
            logger.info(f"Cloning {repo_name} from {repo_url}...")
            
            try:
                cmd = [
                    "git", "clone",
                    "--depth", "100",  # Shallow clone for efficiency
                    "--branch", branch,
                    repo_url,
                    str(repo_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully cloned {repo_name}")
                    cloned_paths.append(repo_path)
                else:
                    logger.error(f"Failed to clone {repo_name}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout cloning {repo_name}")
            except Exception as e:
                logger.error(f"Error cloning {repo_name}: {e}")
        
        return cloned_paths
    
    def run_refactoring_miner(self, repo_path: Path) -> Path:
        """
        Run RefactoringMiner on a repository to extract refactoring history.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Path to the output JSON file
        """
        output_dir = Path(self.config["data"].get("refactoring_dir", "data/refactoring_miner"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{repo_path.name}-refactorings.json"
        
        if output_file.exists():
            logger.info(f"RefactoringMiner output already exists: {output_file}")
            return output_file
        
        logger.info(f"Running RefactoringMiner on {repo_path.name}...")
        
        try:
            # RefactoringMiner command
            cmd = [
                "java", "-jar", "tools/RefactoringMiner.jar",
                "-a", str(repo_path),
                "-json", str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"RefactoringMiner completed for {repo_path.name}")
            else:
                logger.warning(f"RefactoringMiner failed: {result.stderr}")
                
        except FileNotFoundError:
            logger.warning("RefactoringMiner not found. Skipping ground truth extraction.")
        except Exception as e:
            logger.error(f"Error running RefactoringMiner: {e}")
        
        return output_file
    
    def get_java_file_count(self, repo_path: Path) -> int:
        """Count Java files in repository."""
        count = 0
        for _ in repo_path.rglob("*.java"):
            count += 1
        return count
    
    def get_repository_stats(self) -> Dict[str, Dict]:
        """Get statistics for all repositories."""
        stats = {}
        
        for repo in self.repositories:
            repo_name = repo["name"]
            repo_path = self.raw_dir / repo_name
            
            if not repo_path.exists():
                stats[repo_name] = {"exists": False}
                continue
            
            java_files = self.get_java_file_count(repo_path)
            
            stats[repo_name] = {
                "exists": True,
                "java_files": java_files,
                "path": str(repo_path)
            }
        
        return stats


if __name__ == "__main__":
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    collector = DataCollector(config)
    
    # Show repository stats
    stats = collector.get_repository_stats()
    for repo, info in stats.items():
        print(f"{repo}: {info}")
