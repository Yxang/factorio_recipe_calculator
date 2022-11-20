import os
import sqlite3

import click
import numpy as np

from calc_util import cli_load_recipes
from db_util import init_db
from recipe import Recipe

FORCE_RECREATE = os.environ.get('FORCE_RECREATE', False)

conn = init_db(force_recreate=FORCE_RECREATE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()


@click.group()
def main():
    pass


@main.command()
@click.option("--name", '-n', help='name of the recipe')
@click.option("--inputs", '-i', multiple=True, help='input items in format \'{number},{name}\'')
@click.option("--outputs", '-o', multiple=True, help='output items in format \'{number},{name}\'')
@click.option("--time", '-t', help='consumed time unit in seconds')
def add_recipe(name, inputs, outputs, time):
    try:
        recipe = Recipe.de((name, ';'.join(inputs), ';'.join(outputs), time))
    except Exception:
        raise Exception("input format error")

    if input("recipe to add: \n{}\nconfirm? (y/n):".format(recipe)) == 'y':
        recipe_ser = recipe.ser()
        try:
            cur.execute("INSERT INTO recipe VALUES (?, ?, ?, ?)", recipe_ser)
            conn.commit()
        except sqlite3.IntegrityError:
            current_recipe = Recipe.de(cur.execute("SELECT * FROM recipe WHERE recipe_name = ?", (name,)).fetchone())
            if input("recipe already exists:\n{}\noverwrite? (y/n):".format(current_recipe)) == 'y':
                cur.execute("UPDATE recipe SET inputs=?, outputs=?, time=? WHERE recipe_name=?",
                            (recipe_ser[1], recipe_ser[2], recipe_ser[3], recipe_ser[0]))
                conn.commit()
            else:
                print("recipe not added")

    else:
        print("recipe not added")


@main.command()
def list_recipes():
    recipes = cur.execute("SELECT * FROM recipe").fetchall()
    for recipe in recipes:
        print(Recipe.de(recipe))


@main.command()
@click.option("--cli", is_flag=True, default=True, show_default=True, help='if use cli to input')
@click.option("--json", is_flag=True, default=False, show_default=True, help='name of the recipe')
@click.option("--input-path", '-p', help='path to input json file')
def calc(cli, json, input_path):
    if cli == json:
        raise Exception("only one of cli or json can be true")

    if json:
        raise NotImplementedError("json input not implemented")

    recipes = list()
    item_id_dict = dict()
    objectives = dict()

    print('========================')
    print('adding recipes')
    print('========================')
    if cli:
        recipes = cli_load_recipes(cur)

    # 0. find all unique items
    for recipe in recipes:
        for item in recipe.recipe.inputs:
            if item[1] not in item_id_dict:
                item_id_dict[item[1]] = len(item_id_dict)
        for item in recipe.recipe.outputs:
            if item[1] not in item_id_dict:
                item_id_dict[item[1]] = len(item_id_dict)

    # 1. ask for objective
    if cli:
        print('========================')
        print('input objectives')
        print()
        print('input float number for constraints, positive for output and negative for input')
        print('or \'w\' or \'whatever\' for depending on other items:')
        print('========================')
        for item in item_id_dict:
            objective = input('objective for {} (see above info): '.format(item))
            if objective == 'whatever' or objective == 'w':
                objectives[item] = 'whatever'
            else:
                objectives[item] = float(objective)
    print('========================')
    print('All inputs')
    print('========================')

    print('recipes: {}', '\n'.join([str(recipe) for recipe in recipes]))
    print('objectives: {}'.format({k: v for k, v in objectives.items()}))

    # 2. create matrix
    matrix = np.zeros((len(item_id_dict), len(recipes)))
    obj_vector = np.zeros(len(item_id_dict))
    for recipe_index, recipe in enumerate(recipes):
        # 2.1 normalize the item number
        inputs = [(item[0] / recipe.recipe.time / recipe.factory_base_speed / (1 + recipe.speed / 100),
                   item[1])
                  for item in recipe.recipe.inputs]
        outputs = [(item[0] / recipe.recipe.time / recipe.factory_base_speed / (1 + recipe.speed / 100) *
                    (1 + recipe.productivity / 100),
                    item[1])
                   for item in recipe.recipe.outputs]
        # 2.2 add to matrix
        for input_item in inputs:
            matrix[item_id_dict[input_item[1]], recipe_index] -= input_item[0]
        for output_item in outputs:
            matrix[item_id_dict[output_item[1]], recipe_index] += output_item[0]

    for k, objective in objectives.items():
        if objective != 'whatever':
            obj_vector[item_id_dict[k]] = objective

    # 3. solve
    to_solve_indices = [item_id_dict[item] for item, obj in objectives.items() if obj != 'whatever']
    to_solve_mat = matrix[to_solve_indices, :]
    to_solve_obj = obj_vector[to_solve_indices]
    ext_to_solve_mat = np.hstack((to_solve_mat, to_solve_obj.reshape(-1, 1)))

    print('========================')
    print('Solution')
    print('========================')
    if np.linalg.matrix_rank(to_solve_mat) == np.linalg.matrix_rank(ext_to_solve_mat) == len(to_solve_indices):
        solution = np.linalg.solve(to_solve_mat, to_solve_obj)
        if not np.all(solution >= 0):
            print('WARNING: negative solution, check your input')
        for i, recipe in enumerate(recipes):
            print('{:3d} -- {}'.format(i, recipe))
            print('    name: {}'.format(recipe.recipe.recipe_name))
            print('    raw recipe count: {}'.format(solution[i]))
            print('    factory count: {}'.format(solution[i] / recipe.factory_base_speed / recipe.recipe.time))
            print('    inputs:')
            for input_item in recipe.recipe.inputs:
                print('        {} -- {:3f}'.format(input_item[1],
                                                   input_item[0] *
                                                   solution[i]
                                                   / recipe.factory_base_speed
                                                   / recipe.recipe.time))
            print('    outputs:')
            for output_item in recipe.recipe.outputs:
                print('        {} -- {:3f}'.format(output_item[1],
                                                   output_item[0] *
                                                   solution[i] *
                                                   (1 + recipe.productivity / 100)
                                                   / recipe.factory_base_speed
                                                   / recipe.recipe.time))

    elif np.linalg.matrix_rank(to_solve_mat) == np.linalg.matrix_rank(ext_to_solve_mat) < len(to_solve_indices):
        print('Infinite solutions. Add more constraints.')
    elif np.linalg.matrix_rank(to_solve_mat) < np.linalg.matrix_rank(ext_to_solve_mat):
        print('No solution. please check your input recipes and constraints.')
    else:
        raise Exception('Error in solving equation')


if __name__ == '__main__':
    main()
