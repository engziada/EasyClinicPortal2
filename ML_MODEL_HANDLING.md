# Handling Large ML Model Files

This document provides guidance on working with the large ML model files in this repository.

## About the ML Model

- **File**: `mlmodel/SkinD_model_V1.keras`
- **Size**: 148 MB
- **Purpose**: Skin disease classification (Melanoma, Acne, Eczema)
- **Architecture**: EfficientNetB3-based neural network

## Git LFS Setup

This repository uses Git Large File Storage (Git LFS) to handle the large model file. Git LFS replaces large files with text pointers in Git, while storing the file contents on a remote server.

### For New Contributors

1. Install Git LFS:
   ```
   # For Windows
   git lfs install
   
   # For macOS (using Homebrew)
   brew install git-lfs
   git lfs install
   
   # For Ubuntu/Debian
   sudo apt-get install git-lfs
   git lfs install
   ```

2. Clone the repository normally:
   ```
   git clone https://github.com/engziada/EasyClinicPortal2.git
   ```

3. Git LFS will automatically download the large files when you checkout the branch.

### Adding New Large Files

If you need to add a new large file (like an updated model version):

1. Make sure the file extension is tracked by Git LFS:
   ```
   git lfs track "*.keras"  # Already set up in this repo
   ```

2. Add and commit the file normally:
   ```
   git add path/to/large/file.keras
   git commit -m "Add new model file"
   ```

3. Push to GitHub:
   ```
   git push origin branch-name
   ```

## Alternative Approaches

If Git LFS doesn't work for your workflow, consider these alternatives:

1. **Model Hosting Services**: Host the model on TensorFlow Hub, Hugging Face, or similar services.

2. **Cloud Storage**: Store the model in AWS S3, Google Cloud Storage, or Azure Blob Storage and download it at runtime.

3. **Release Assets**: Upload the model as a release asset on GitHub and provide a script to download it.

## Troubleshooting

If you encounter issues with Git LFS:

1. Verify Git LFS is installed: `git lfs version`
2. Check tracked files: `git lfs ls-files`
3. For download issues: `git lfs pull`
4. For upload issues: Check your Git LFS quota on GitHub

## References

- [Git LFS Documentation](https://git-lfs.github.com/)
- [GitHub's File Size Limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
