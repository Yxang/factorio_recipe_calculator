from recipe import Recipe, RecipeInstance


def cli_load_recipes(cur):
    recipes = list()
    available_recipes = [Recipe.de(recipe) for recipe in cur.execute('SELECT * FROM recipe').fetchall()]
    while True:
        recipe_name = input('recipe name or index, '
                            '\'l\' for list of index and recipes, '
                            '\'s:{name}\' for search, '
                            '\'c\' for current added recipes, '
                            '\'done\' for done: ')
        if recipe_name == 'l':
            for i, recipe in enumerate(available_recipes):
                print('{:3d} -- {}'.format(i, recipe))
        elif recipe_name.startswith('s:'):
            for i, recipe in enumerate(available_recipes):
                if recipe_name[2:] in recipe.recipe_name:
                    print('{:3d} -- {}'.format(i, recipe))
        elif recipe_name == 'c':
            print('current add recipes: ')
            for recipe in recipes:
                print(recipe)
        elif recipe_name == 'done':
            break
        else:
            print('adding recipe {}...'.format(recipe_name))
            if recipe_name.isnumeric():
                recipe_name = int(recipe_name)
                if recipe_name >= len(available_recipes):
                    print('invalid recipe index')
                    continue
                recipe = available_recipes[recipe_name]
            else:
                recipe_name = [recipe for recipe in available_recipes if recipe.recipe_name == recipe_name]
                if len(recipe_name) == 0:
                    print('invalid recipe name')
                    continue
                recipe = recipe_name[0]
            factory_base_speed = float(input('  factory base speed: ').strip())
            if factory_base_speed <= 0:
                print('  speed must be positive')
                continue
            speed = float(input('  speed from module (and tech, etc.) in percentage: ').strip().strip('%'))
            if speed <= -100:
                print('  speed must be positive')
                continue
            productivity = float(input('  productivity from module (and tech, etc.) in percentage: ').strip().strip('%'))
            if productivity <= -100:
                print('  speed must be positive')
                continue
            recipe_instance = RecipeInstance(recipe, speed, productivity, factory_base_speed)
            print('  {}'.format(recipe_instance))
            if input('  confirm? (y/n): ') == 'y':
                recipes.append(recipe_instance)
    return recipes
