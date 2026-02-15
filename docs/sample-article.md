

Search
Write
Sign up

Sign in



Installing OpenClaw on AWS EC2 (Step-by-Step Production-Ready Guide)
Muhammad Anwar
Muhammad Anwar

Follow
4 min read
·
4 days ago
1


1



OpenClaw is a powerful AI agent framework that integrates Anthropic, OpenAI, Telegram, and multiple skills into a single interactive workflow.
This guide walks you through installing OpenClaw on an AWS EC2 Ubuntu instance, configured for stability and real-world usage.

Prerequisites
Before starting, ensure you have the following:

Infrastructure
EC2 Instance: t3.large
Storage: Minimum 30 GB
OS: Ubuntu Linux (20.04 or 22.04 recommended)
Software & Accounts
NVM
Node.js v22
Git
Anthropic API Key
OpenAI API Key
Google Gemini API Key
Telegram Bot Token Created from Open Bot
Step 1: Install NVM and Node.js 22
Use the script below to install NVM and Node.js in an idempotent and production-safe way.

#!/bin/bash
set -e
set -o pipefail
# ---- 1️⃣ Update system ----
echo "Updating and upgrading system..."
sudo apt update -y
sudo apt upgrade -y
# ---- 2️⃣ Install prerequisites ----
echo "Installing prerequisites..."
sudo apt install -y curl build-essential libssl-dev
# ---- 3️⃣ Install NVM (idempotent) ----
export NVM_DIR="$HOME/.nvm"
if [ ! -d "$NVM_DIR" ]; then
    echo "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
else
    echo "NVM already installed."
fi
# ---- 4️⃣ Load NVM ----
echo "Loading NVM..."
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
# ---- 5️⃣ Install Node.js 22 ----
if ! nvm ls 22 >/dev/null 2>&1; then
    echo "Installing Node.js v22..."
    nvm install 22
else
    echo "Node.js v22 already installed."
fi
echo "Setting Node.js v22 as default..."
nvm alias default 22
nvm use default
# ---- 6️⃣ Verify installation ----
echo "Node version:"
node -v
echo "NPM version:"
npm -v
echo "NVM and Node.js setup complete ✅"
👉 Why Node 22?
OpenClaw relies on modern Node features that are stable in Node.js 22.

Step 2: Set Ubuntu Password & Remount Filesystem
This is required if you need interactive access or certain package installations.

sudo passwd ubuntu
sudo mount -o remount,rw /
Step 3: Install Homebrew (Linuxbrew)
OpenClaw uses Homebrew for dependency management.

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
After installation, follow the terminal instructions to add Homebrew to your PATH.

Step 4: Install OpenClaw
Install OpenClaw using the official installer:

curl -fsSL https://openclaw.ai/install.sh | bash
Step 5: OpenClaw Initial Setup (TUI Configuration)
During installation, select the following options carefully:

General Setup
✅ Select Yes
✅ Select QuickStart
✅ Select Anthropic
🔑 Enter your Anthropic API Key
Press enter or click to view image in full size

Model Selection
Select:
anthropic/claude-sonnet-4-5
Press enter or click to view image in full size

Telegram Integration
Select Telegram (Bot API)
Press enter or click to view image in full size

🔑 Enter your Telegram Bot Token
Press enter or click to view image in full size

Step 6: Skills Selection
When prompted to select skills, press the spacebar to select.

Skip These Skills (Not Supported on EC2/Ubuntu)
❌ 1password
❌ applenotes
❌ camsnap
❌ modal-usage
❌ summarize
Proceed with all other compatible skills.

Press enter or click to view image in full size

Step 7: API Keys Configuration
You will be prompted to enter the following:

🔑 Gemini API Key
Press enter or click to view image in full size

🔑 OpenAI API Key
Press enter or click to view image in full size

Enable hooks Confirm selections using the spacebar when prompted select all three.

Press enter or click to view image in full size

Step 8: Enable Hatch (TUI Mode)
Select Hatch in the TUI interface
Press enter or click to view image in full size

This enables OpenClaw’s interactive terminal UI for real-time operations.

Step 9: Pair Telegram with OpenClaw
Finally, approve Telegram pairing:

openclaw pairing approve telegram <pairing-code>
Replace <pairing-code> with the code shown in your OpenClaw TUI.

Get Muhammad Anwar’s stories in your inbox
Join Medium for free to get updates from this writer.

Enter your email
Subscribe
✅ Once approved, OpenClaw is fully connected to Telegram.

Final Thoughts
You now have OpenClaw running on AWS EC2, powered by:

Claude Sonnet
OpenAI
Gemini
Telegram Bot Interface
This setup is production-ready, scalable, and ideal for AI automation, agent workflows, and chat-based orchestration.

If you’re running this in production, consider:

Using AWS Secrets Manager for API keys
Running OpenClaw under tmux or systemd
Enabling EC2 security hardening
Happy Building 🚀
If this helped you, consider sharing or clapping on Medium to help others deploy OpenClaw smoothly.

Openclaw
Openclaw Bot
Ec2
Installation
AI Agent
1


1


Muhammad Anwar
Written by Muhammad Anwar
1 follower
·
2 following

Follow
Responses (1)

Write a response

What are your thoughts?

Cancel
Respond
Noman Mustafa
Noman Mustafa

4 days ago


Very helpful.
Reply

More from Muhammad Anwar
🚀 Installing MySQL Server and Workbench on Ubuntu 24.04
Muhammad Anwar
Muhammad Anwar

🚀 Installing MySQL Server and Workbench on Ubuntu 24.04
In this guide, we’ll install MySQL Server 8.0 and MySQL Workbench on Ubuntu 24.04. This setup is useful if you’re developing apps locally…
Sep 26, 2025
1
🚀 Self-Hosting OSRM on AWS EC2 for Free Delivery Distance & Time Calculation
Muhammad Anwar
Muhammad Anwar

🚀 Self-Hosting OSRM on AWS EC2 for Free Delivery Distance & Time Calculation
(Rawalpindi & Islamabad — Production Ready Guide)
Jan 20
To add a custom Root domain or Subdomain to a specific branch of your app (on Amplify), and your…
Muhammad Anwar
Muhammad Anwar

To add a custom Root domain or Subdomain to a specific branch of your app (on Amplify), and your…
PREREQUISITE:  Hosted Zone is already created on ROUTE53
Aug 6, 2025
🚀 How to Migrate a Local MySQL Database to AWS EC2
Muhammad Anwar
Muhammad Anwar

🚀 How to Migrate a Local MySQL Database to AWS EC2
If you have a local MySQL database (for example, devops_demo) with tables and data, and you want to move it to your AWS EC2 instance, the…
Sep 26, 2025
See all from Muhammad Anwar
Recommended from Medium
Run OpenClaw (MoltBot, ClawdBot) Safely with Docker: A Practical Guide for Beginners
Towards Dev
In

Towards Dev

by

Bill WANG

Run OpenClaw (MoltBot, ClawdBot) Safely with Docker: A Practical Guide for Beginners
Every few months, a new open‑source AI project catches fire. This time, it’s OpenClaw (formerly MoltBot, Clawdbot — renamed under pressure…

Jan 30
55
3
Running OpenCode with Local LLMs on an M3 Ultra 512GB
Diko Ko
Diko Ko

Running OpenCode with Local LLMs on an M3 Ultra 512GB
1. Introduction

Feb 8
167
1
OpenClaw Security: My Complete Hardening Guide for VPS and Docker Deployments
Reza Rezvani
Reza Rezvani

OpenClaw Security: My Complete Hardening Guide for VPS and Docker Deployments
A practical guide to securing your AI assistant — from first install to production-ready deployment

Feb 2
162
3
10 OpenClaw Use Cases for a Personal AI Assistant
Balazs Kocsis
Balazs Kocsis

10 OpenClaw Use Cases for a Personal AI Assistant
How are people actually using OpenClaw, and how are they integrating it?

Jan 27
72
2
3 Things You Must Build Immediately With OpenClaw (If You Want Real Autonomy)
Coding Nexus
In

Coding Nexus

by

Civil Learning

3 Things You Must Build Immediately With OpenClaw (If You Want Real Autonomy)
If you’re running OpenClaw seriously, there’s a moment you eventually hit.

5d ago
224
Stop Watching OpenClaw Install Tutorials — This Is How You Actually Tame It
Activated Thinker
In

Activated Thinker

by

Shane Collins

Stop Watching OpenClaw Install Tutorials — This Is How You Actually Tame It
Everyone can run npm install. Only a few know how to turn this chaotic AI agent into a tireless digital employee

Feb 1
328
4
See more recommendations
Help

Status

About

Careers

Press

Blog

Privacy

Rules

Terms

Text to speech