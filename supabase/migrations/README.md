# Database Migrations

This directory contains all database migration scripts for the Micro Gallery Japan platform.

## Migration Files

The migrations are numbered sequentially and should be applied in order:

1. `20260119000000_create_artists_table.sql` - Artists user table
2. `20260119000001_create_customers_table.sql` - Customers user table
3. `20260119000002_create_corporates_table.sql` - Corporates user table
4. `20260119000003_update_artists_table.sql` - Add additional fields to artists table
5. `20260119000004_create_admins_table.sql` - Admin users table
6. `20260119000005_create_bank_accounts_table.sql` - Bank account information
7. `20260119000006_create_artworks_table.sql` - Artwork catalog
8. `20260119000007_create_artwork_images_table.sql` - Artwork images
9. `20260119000008_create_corporate_spaces_table.sql` - Corporate display spaces
10. `20260119000009_create_space_artwork_assignments_table.sql` - Artwork display assignments
11. `20260119000010_create_orders_table.sql` - Customer orders
12. `20260119000011_create_payments_table.sql` - Payment transactions
13. `20260119000012_create_transactions_table.sql` - Financial transactions
14. `20260119000013_create_display_history_table.sql` - Display history tracking
15. `20260119000014_create_artwork_analytics_table.sql` - Artwork analytics
16. `20260119000015_create_qr_code_scans_table.sql` - QR code scan tracking
17. `20260119000016_create_customer_favorites_table.sql` - Customer favorites
18. `20260119000017_create_corporate_favorites_table.sql` - Corporate favorites
19. `20260119000018_create_artwork_inquiries_table.sql` - Artwork inquiries
20. `20260119000019_create_shipments_table.sql` - Shipping records
21. `20260119000020_create_shipping_tracking_table.sql` - Shipping tracking events
22. `20260119000021_create_addresses_table.sql` - User addresses
23. `20260119000022_create_issue_reports_table.sql` - Issue reports
24. `20260119000023_create_return_requests_table.sql` - Return requests
25. `20260119000024_create_schema_migrations_table.sql` - Migration tracking table

## How to Apply Migrations

### Option 1: Using Supabase CLI (Recommended)

1. **Install Supabase CLI** (if not already installed):
   ```bash
   npm install -g supabase
   ```

2. **Link to your Supabase project**:
   ```bash
   supabase link --project-ref your-project-ref
   ```

3. **Apply all migrations**:
   ```bash
   supabase db push
   ```

   Or apply migrations individually:
   ```bash
   supabase migration up
   ```

### Option 2: Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste each migration file content in order
4. Execute each migration sequentially

### Option 3: Using psql (Direct Database Connection)

1. **Connect to your Supabase database**:
   ```bash
   psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
   ```

2. **Apply migrations**:
   ```bash
   \i backend/supabase/migrations/20260119000000_create_artists_table.sql
   \i backend/supabase/migrations/20260119000001_create_customers_table.sql
   # ... continue for all migrations
   ```

   Or apply all at once:
   ```bash
   for file in backend/supabase/migrations/*.sql; do
     psql "postgresql://..." -f "$file"
   done
   ```

## Important Notes

### Row Level Security (RLS)

All tables have Row Level Security (RLS) enabled with appropriate policies:
- Users can only access their own data
- Public read access for published content (artworks)
- Service role has full access for backend operations

### Foreign Key Dependencies

Migrations are ordered to respect foreign key dependencies:
- User tables (artists, customers, corporates) are created first
- Artworks depend on artists
- Orders depend on customers and artworks
- All other tables follow their dependencies

### Existing Data

⚠️ **Warning**: These migrations use `CREATE TABLE IF NOT EXISTS`, so they won't fail if tables already exist. However, if you need to modify existing tables, you may need to create new migration files.

### Rollback

To rollback migrations, you would need to create corresponding rollback scripts. Currently, these are not included but can be created following the pattern:
- `YYYYMMDDHHMMSS_description_rollback.sql`

## Verification

After applying migrations, verify the schema:

```sql
-- Check all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Check indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

## Troubleshooting

### Error: "relation already exists"
- Some tables may already exist from previous migrations
- The `IF NOT EXISTS` clause should handle this, but if errors persist, check which tables already exist

### Error: "function update_updated_at_column() does not exist"
- This function is created in the first artists migration
- Make sure migrations are applied in order

### Error: "permission denied"
- Ensure you're using the service role key or have appropriate permissions
- Check RLS policies if accessing via client libraries

## Migration Tracking

The `schema_migrations` table tracks which migrations have been applied. You can query it:

```sql
SELECT * FROM schema_migrations ORDER BY applied_at;
```

## Next Steps

After applying migrations:
1. Verify all tables are created correctly
2. Test RLS policies with different user roles
3. Set up initial admin user if needed
4. Configure any additional indexes based on query patterns
