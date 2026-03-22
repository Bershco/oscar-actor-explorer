Task 2: Oscar Actor Explorer (25pt)
Dataset: The Oscar Award
Requirement: Use an ORM :PonyORM, SQLAlchemy, or Peewee (your choice). No raw
SQL allowed for this task.
Task 2.1 :Data Modeling with ORM (5pt)
• Load the dataset into SQLite using your chosen ORM.
• Define proper entity/model classes with appropriate types, relationships, and
constraints.
• In a markdown cell: briefly explain your schema design and why you chose this ORM
over others.
Task 2.2: Actor Profile App (10pt)
Build an interactive app or widget. The user enters an actor or director name and gets
a rich profile card that combines:
From the dataset:
• Number of nominations and wins
• Categories nominated in
• Years active at the Oscars
• List of nominated and winning films
From Wikipedia (fetched live via the Wikipedia API or the wikipedia Python package):
• Short biography summary
• Birth date and photo (if available)
Computed insights:
• Win rate (wins / nominations)
• Comparison to the average nominee in their category
• Years between first nomination and first win (if applicable)
Handle edge cases gracefully: actor not found in dataset, ambiguous Wikipedia matches,
actors with no wins, etc.
Task 2.3 :Interesting Finds (10pt)
Use your app and/or ORM queries to find and report 3 interesting discoveries. For each:
state the finding, show how you found it, and explain why it's interesting.
Examples of what might count:
• Actors with the most nominations but zero wins
• The longest gap between first nomination and first win
• Directors who were also nominated as actors (or vice versa)
• Categories with the most unique winners (hardest to predict)
• Actors or films with nominations across the most di`erent categories
Bonus (5pt): Add a "Did You Know?" feature that auto-generates a fun fact when the user
looks up any actor (e.g., "Meryl Streep has more nominations than 85% of all Oscar-
nominated actors").
