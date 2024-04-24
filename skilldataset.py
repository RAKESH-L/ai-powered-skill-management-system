def combine_and_calculate_weighted_average(technical_skills, github_languages):
    combined_percentages = {}

    # Combine technical_skills and github_languages into a single dictionary
    combined_data = {}
    for word, percentage, total_count_in_entity_group in technical_skills:
        combined_data[word] = {'technical_percentage': percentage, 'total_count_in_entity_group': total_count_in_entity_group}

    for language, percentage in github_languages:
        if language in combined_data:
            combined_data[language]['github_percentage'] = percentage
        else:
            combined_data[language] = {'github_percentage': percentage, 'technical_percentage': 0, 'total_count_in_entity_group': 0}

    # Calculate the weighted average for each word or skill or language
    for word, data in combined_data.items():
        technical_percentage = data.get('technical_percentage', 0)
        github_percentage = data.get('github_percentage', 0)
        total_count = data.get('total_count_in_entity_group', 0)

        weighted_average = ((technical_percentage * total_count) + github_percentage) / (total_count + 1)
        combined_percentages[word] = weighted_average

    return combined_percentages

# Example usage
employee_id = 123  # Replace with the actual employee ID
technical_skills = [('Java', 25, 16), ('Python', 65, 5), ('C', 10, 1)]
github_languages = [('Java', 20), ('Python', 80)]

combined_percentages = combine_and_calculate_weighted_average(technical_skills, github_languages)
print(combined_percentages)
