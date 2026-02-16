# Supabase CLI Setup

This directory contains Supabase configuration and migrations managed by Supabase CLI.

## Setup

### 1. Link to Test Project (First Time)
```bash
npx supabase link --project-ref your-project-ref
```
Get your project ref from: Supabase Dashboard → Project Settings → General → Reference ID

### 2. Push Migrations to Test Project
```bash
npx supabase db push
```

### 3. For Production (When Ready)
```bash
# Link to production project
npx supabase link --project-ref production-project-ref

# Push all migrations
npx supabase db push
```

## Migration Workflow

### Create New Migration
```bash
npx supabase migration new migration_name
```
This creates a timestamped file in `supabase/migrations/`

### Apply Migrations
```bash
# Push to linked project
npx supabase db push

# Or reset local (if using local dev)
npx supabase db reset
```

## Migration Files

Migration files are in `supabase/migrations/` with timestamp format:
- `YYYYMMDDHHMMSS_description.sql`

Example:
- `20260119000000_create_artists_table.sql`

## Commands Reference

- `npx supabase init` - Initialize Supabase in project
- `npx supabase link --project-ref <ref>` - Link to remote project
- `npx supabase migration new <name>` - Create new migration
- `npx supabase db push` - Push migrations to linked project
- `npx supabase db pull` - Pull schema from remote
- `npx supabase db diff` - Generate diff between local and remote
