import streamlit as st
import mysql.connector
import pandas as pd

# Connect to MySQL database
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="bus_details"
    )

# Function to fetch distinct route names starting with a specific letter
def fetch_route_names(connection, starting_letter):
    query = "SELECT DISTINCT Route_Name FROM bus_info WHERE Route_Name LIKE %s ORDER BY Route_Name"
    cursor = connection.cursor()
    cursor.execute(query, (starting_letter + '%',))
    route_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return route_names

# Function to fetch data based on selected Route_Name and price sort order
def fetch_data(connection, route_name, price_sort_order):
    price_sort_order_sql = "ASC" if price_sort_order == "Low to High" else "DESC"
    query = f"""
        SELECT * FROM bus_info 
        WHERE Route_Name = %s 
        ORDER BY Star_Rating DESC, Price {price_sort_order_sql}
    """
    df = pd.read_sql(query, connection, params=(route_name,))
    return df

# Function to filter data based on Star_Rating and Bus_Type
def filter_data(df, star_ratings, bus_types):
    return df[df['Star_Rating'].isin(star_ratings) & df['Bus_Type'].isin(bus_types)]

# Main Streamlit app
def main():
    st.title('🚌 Easy and Secure Online Bus Ticket Booking')

    # Connect to MySQL
    connection = get_connection()

    try:
        # Sidebar - Input for starting letter
        starting_letter = st.sidebar.text_input('🔍 Enter first letter of Route Name:', 'A').upper()

        if starting_letter:
            # Fetch route names
            route_names = fetch_route_names(connection, starting_letter)

            if route_names:
                # Sidebar - Selectbox for Route_Name
                selected_route = st.sidebar.radio('📍 Select Route Name', route_names)

                if selected_route:
                    # Sidebar - Sort by Price
                    price_sort_order = st.sidebar.selectbox('💲 Sort by Price', ['Low to High', 'High to Low'])

                    # Fetch data for selected route
                    data = fetch_data(connection, selected_route, price_sort_order)

                    if not data.empty:
                        # Display data
                        st.subheader(f"🛣️ Bus Details for Route: {selected_route}")
                        st.dataframe(data)

                        # Filters: Star Rating & Bus Type
                        star_ratings = sorted(data['Star_Rating'].dropna().unique().tolist(), reverse=True)
                        selected_ratings = st.multiselect('⭐ Filter by Star Rating', star_ratings, default=star_ratings)

                        bus_types = sorted(data['Bus_Type'].dropna().unique().tolist())
                        selected_bus_types = st.multiselect('🚌 Filter by Bus Type', bus_types, default=bus_types)

                        if selected_ratings and selected_bus_types:
                            filtered_data = filter_data(data, selected_ratings, selected_bus_types)
                            st.subheader("🎯 Filtered Results")
                            st.dataframe(filtered_data)
                    else:
                        st.warning(f"No buses found for route **{selected_route}**.")
            else:
                st.warning("🚫 No routes found starting with the specified letter.")
    finally:
        connection.close()

if __name__ == '__main__':
    main()
