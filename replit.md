# Discord Server Template Bot

## Overview

A fully functional Discord bot that creates professional server templates with categories, text channels, voice channels, and roles. The bot provides a complete server setup solution through the `k!template` command, allowing users to either create a default professional server structure or describe custom templates like "gaming-type as a studio". The bot includes comprehensive moderation commands, AFK system, music controls, verification system, and various utility commands to enhance server management and user experience.

## Recent Changes (September 10, 2025)

- ✅ **DYNAMIC TEMPLATE SYSTEM**: Completely overhauled k!template command to create custom server templates based on any description - now supports unlimited server types like "memes", "art community", "gaming clan", "coding", etc.
- ✓ **DM NOTIFICATIONS**: Added DM notifications for k!commandban and k!commandmute commands - users now receive direct messages when banned/muted from using bot commands
- ✓ **SECURE OWNER AUTHENTICATION**: Fixed critical security vulnerability by replacing username-based owner checks with immutable Discord user ID system 
- ✓ **BOT OWNER MANAGEMENT**: Created k!addowner, k!removeowner, and k!owners commands allowing original owners to grant admin management privileges to other users
- ✓ **COMMAND RESTRICTION FIXES**: Command bans and mutes now only block actual k! commands, not regular chat messages from users

## Previous Changes (August 21, 2025)

- ✓ **GLOBAL COMMAND RESTRICTIONS**: Made k!commandban and k!commandmute global by default - applies across ALL servers (kh2.officialeditz & r3act0r_editzofficial only)
- ✓ **SELECTIVE SLASH COMMANDS**: Only owner-only commands (commandban, commandmute, etc.) work as slash commands, all others blocked with k! prefix redirect message
- ✓ **NSFW CONTENT DETECTION**: Added black screen detection for k!image command that warns users when images are fully black (usually means NSFW content filtered)
- ✓ **NO SLASH COMMANDS**: Completely removed all slash commands - bot now uses k! prefix commands only throughout entire system
- ✓ **IMAGE GENERATION COG**: Integrated AI image generation using Pollinations API with k!image command (kh2.officialeditz & r3act0r_editzofficial only)
- ✓ **TEMPROLES COMMAND**: Added k!temproles for role template creation with gaming, appeal, staff, and community templates
- ✓ **GLOBAL DELETEALL CONTROLS**: Added dual-owner k!globaldeleteall-online/offline commands for bot-wide deleteall management (kh2.officialeditz & r3act0r_editzofficial)
- ✓ **MESSAGE DUPLICATION FIX**: Fixed message duplication issues in bot command processing system
- ✓ **DELETEALL COMMAND**: Modified k!deleteall to delete ALL channels (text/voice) with administrator permissions and enable/disable toggle system
- ✓ **ADMIN SETTINGS**: Created admin_settings table to store server-specific feature toggles and configurations
- ✓ **SAFETY FEATURES**: Implemented double confirmation system for deleteall (confirm parameter + reaction confirmation)
- ✓ **APPEAL TEMPLATE SYSTEM**: Added complete appeal server template with <==Staff==>, <==Information==>, <==Appeal Here!==> categories
- ✓ **ROLE CREATION**: Automatic creation of Owner, Co-Owner, Manager (admin perms), Administrator & Moderator (moderation perms) for appeal servers
- ✓ **GLOBAL COMMAND BANS**: Command bans now apply globally across all servers by default, with database support for global restrictions
- ✓ **ENHANCED PERMISSIONS**: Granular channel permissions for staff roles with proper hierarchy access control
- ✓ **DATABASE UPDATES**: Added is_global column to command_restrictions table for cross-server ban functionality
- ✓ **TEMPLATE IMPROVEMENTS**: Staff channels now properly restrict access based on role hierarchy (moderator-chat, administrator-chat, manager-chat)

## Previous Changes (August 19, 2025)

- ✓ **CRITICAL FIX**: Fixed get_prefix method signature error that was preventing message processing
- ✓ **@everyone Role Protection**: Modified template system to preserve existing @everyone role permissions instead of overwriting them
- ✓ **Bot Architecture**: Established proper cog-based structure with all 8 modules loading successfully
- ✓ **Database Integration**: Fully functional SQLite database with persistent storage for guild settings, moderation logs, AFK status, and command restrictions
- ✓ **Command Processing**: Resolved TypeError that was causing bot to ignore all messages and commands
- ✓ **Token Integration**: Bot successfully connects and operates with provided Discord token
- ✓ **NEW COMMANDS**: Added say, sayembed, commandban, commandmute, commandwarn with dual-owner permissions (kh2.officialeditz & r3act0r_editzofficial)
- ✓ **Enhanced Help System**: Comprehensive k!help command with special commands visible only to authorized users

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Discord.py 2.x** - Modern Discord bot framework using discord.ext.commands for command handling with full Discord API integration
- **Cog-based Architecture** - Modular command organization using Discord.py's Cog system across 8 specialized modules (template, moderation, general, afk, admin, verification, music, fun)
- **Hybrid Command Interface** - Both traditional prefix commands (k!) and slash commands for key functionality like template creation
- **Permission-based Access Control** - Administrator permission requirements for template commands and role-based restrictions throughout the system

### Database Architecture
- **SQLite with aiosqlite** - Asynchronous SQLite database for persistent data storage with connection pooling
- **Guild-specific Configuration** - Per-server settings including custom prefixes, modlog channels, welcome channels, and autoroles
- **Moderation Logging System** - Comprehensive case tracking with auto-incrementing case IDs, timestamps, and action history
- **AFK Status Management** - User AFK state tracking with timestamps and custom messages across guilds
- **Verification System** - User verification status tracking for member validation workflows

### Template System Design
- **Default Template Structure** - Predefined server layout with 5 main categories (Information, General, Extra, Voice Chat, Staff Only) containing 25+ channels with emoji prefixes
- **Custom Template Support** - Natural language template generation that interprets user descriptions like "gaming-type as a studio" for specialized server layouts
- **Progressive Creation Workflow** - Multi-stage setup process with real-time status updates ("Creating Categories..." → "Creating Text Channels" → "Creating Roles" → "Completed!")
- **Permission Validation System** - Comprehensive bot permission checking before template creation with detailed error messaging when permissions are insufficient
- **Role Hierarchy Management** - Automated creation of structured role systems with proper permission inheritance and staff role organization

### Channel Architecture
- **Category-based Organization** - Logical grouping using Discord categories with standardized emoji prefixes for visual consistency
- **Mixed Channel Types** - Support for both text and voice channels within unified template structures
- **Permission Inheritance** - Staff-only sections with cascading permission restrictions and role-based channel visibility
- **Standardized Naming Convention** - Consistent emoji usage and professional naming patterns for server aesthetics

### Moderation Framework
- **Comprehensive Action System** - Full moderation suite including kick, ban, warn, mute with reason logging and case tracking
- **Database Integration** - All moderation actions logged with case numbers, timestamps, moderator tracking, and reason storage
- **Permission Hierarchy Respect** - Role-based moderation restrictions preventing abuse of authority
- **Automated Logging** - Optional modlog channel integration for server-wide moderation transparency

### Utility Systems
- **Custom Embed Framework** - Standardized Discord embed creation system for success, error, and informational messages with consistent branding
- **AFK Management** - Automatic AFK status detection with mention notifications and return-time tracking
- **Verification Workflow** - User verification system with role assignment and status persistence
- **Music Integration** - Basic voice channel connection and music playback framework (placeholder for extended functionality)

### Error Handling Strategy
- **Permission-aware Responses** - Context-sensitive error messages when bot lacks necessary permissions with clear user guidance
- **Graceful Degradation** - Informative feedback system that continues operation when some features are unavailable
- **Async Operation Safety** - Non-blocking template creation with proper error propagation and transaction rollback capabilities
- **Logging Infrastructure** - Comprehensive logging system for debugging, monitoring, and operational visibility

## External Dependencies

### Discord Integration
- **Discord.py Library** - Primary framework for Discord API interaction, bot commands, and server management functionality
- **Discord Permissions API** - Native Discord permission system validation for bot capabilities and user authorization checks
- **Discord Guild Management** - Server category, channel, and role creation through Discord's REST API with rate limiting compliance

### Database Layer
- **aiosqlite** - Asynchronous SQLite database driver for persistent data storage without blocking the event loop
- **SQLite Database Engine** - Local file-based database for guild configurations, moderation logs, AFK status, and verification data

### System Dependencies
- **asyncio** - Python's asynchronous I/O framework for concurrent operations and non-blocking database access
- **logging** - Comprehensive logging system for operational monitoring, debugging, and error tracking
- **psutil** - System resource monitoring for bot performance statistics and uptime tracking
- **pathlib** - Modern file system path handling for database file management and asset loading