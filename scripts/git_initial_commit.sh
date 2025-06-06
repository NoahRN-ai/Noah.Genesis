#!/bin/bash

# This script is intended for the initial setup of the Git repository
# for Project Noah.Genesis MVP.
#
# **WARNING:** Run this script only once in a clean project directory
# if you are initializing a new Git repository from these files.
# If you have an existing .git directory, this script might cause issues.

echo "Initializing new Git repository..."
git init -b main
echo "Done."

echo ""
echo "Adding all files to the staging area..."
git add .
echo "Done."

echo ""
echo "Creating initial commit..."
git commit -m "Initial commit of Project Noah.Genesis MVP code and documentation."
echo "Done."

echo ""
echo "Git repository initialized and initial commit created successfully."
echo "You can now add a remote origin and push the repository, for example:"
echo "  git remote add origin <your-remote-repository-url>"
echo "  git push -u origin main"
```
