def classify_open_context(open_price, prev_range):
    """Classifies the open price by checking whether it falls within the quartile tags of the previous range. It only appends quartile tags when the open price is inside the previous range."""
    tags = []
    if open_price >= prev_range[0] and open_price <= prev_range[1]:  # Only consider if inside range
        width = prev_range[1] - prev_range[0]
        quartile_one = prev_range[0] + 0.25 * width
        quartile_two = prev_range[0] + 0.5 * width
        quartile_three = prev_range[0] + 0.75 * width
        if open_price < quartile_one:
            tags.append("Q1")
        elif open_price < quartile_two:
            tags.append("Q2")
        elif open_price < quartile_three:
            tags.append("Q3")
        else:
            tags.append("Q4")
    return tags


def compute_level_game_stats(scenario_data):
    """Generates detailed scenario data for Level Game backtesting."""
    # Implementation for level game stats computation
    stats = {}
    # Add your logic here to populate stats based on scenario_data
    # Example logic
    stats['summary'] = "Level Game Statistics"  # Placeholder
    return stats


def gap_analysis(data):
    """Analyzes gaps based on the fill probability on the same day."""
    # Implementation for gap analysis
    # Example logic
    condition = True  # Placeholder for the actual condition
    # Do gap analysis based on the same-day fill probability
    return condition


def main():
    # Existing main function logic
    aggregate_and_write()
    scenario_data = []  # Get or define your scenario data
    level_game_stats = compute_level_game_stats(scenario_data)  # Call the new function
    # Rest of your main function logic
    
# Ensure this file maintains all existing functionality while implementing the new features accordingly.