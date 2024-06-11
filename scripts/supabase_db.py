from supabase import create_client, Client

class SupabaseDB:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def create(self, table_name: str, data: dict):
        """Insert a new record into the table."""
        response = self.client.table(table_name).insert(data).execute()
        return response.data

    def read(self, table_name: str, query: dict = None, order_by: str = None):
        """Read records from the table. Optional query to filter results and order_by to sort results."""
        table = self.client.table(table_name).select("*")
        if query:
            table = table.match(query)
        if order_by:
            table = table.order(order_by)
        response = table.execute()
        return response.data

    def update(self, table_name: str, match_query: dict, update_data: dict):
        """Update records in the table based on a match query."""
        response = self.client.table(table_name).update(update_data).match(match_query).execute()
        return response.data

    def delete(self, table_name: str, match_query: dict):
        """Delete records from the table based on a match query."""
        response = self.client.table(table_name).delete().match(match_query).execute()
        return response.data