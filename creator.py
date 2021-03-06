import pprint
import os

import yaml
import numpy.random

import roll as r
import add as a
import stats as s


# import yaml file for race weights
races = yaml.load(open("Data/races.yaml", "r"))


# given a list of values with weights, randomly pick one
def random_from(items):
    # make a value weight tuple for each item, them zip them so there is a value array and a weight array
    values, weights = zip(*[(value, items[value]["weight"]) for value in items])
    total = sum(weights)
    probs = [weight / total for weight in weights]
    return numpy.random.choice(values, p=probs)


def create(stats=None):
    # create an array of values to keep track of choices
    attr = []

    # create object to return as created character info
    character = {}

    # choose a random race and add it to the list
    race = random_from(yaml.load(open("Data/races.yaml")))
    attr += [race]

    # choose a random subrace of our chosen race and add it to the list
    subrace = random_from(yaml.load(open("Data/Gen/{}/subraces.yaml".format(*attr))))
    attr += [subrace]

    # choose a random background for our race/subrace choices
    background = random_from(yaml.load(open("Data/Gen/{}/{}/backgrounds.yaml".format(*attr))))

    # save choices to character
    character["background"] = background
    character["race"] = race

    # not all races have subraces
    character["subrace"] = subrace if subrace != "" else None

    # choose a random class for race/subrace choices if we aren't making a colville character
    if stats is None:
        cl = random_from(yaml.load(open("Data/Gen/{}/{}/classes.yaml".format(*attr))))

    # colville method
    else:
        # stats were rolled in order
        character["stats"] = dict(zip(["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                                      stats))

        # print out what we are working with
        print("stats: ", dict(character["stats"]))

        # add racial modifiers
        a.add_details(character)

        # determine class from new scores
        cl = s.get_class(character)

    # save class choice
    attr += [cl]

    # choose random archetype for our choices thus far
    archetype = random_from(yaml.load(open("Data/Gen/{}/{}/{}/archetypes.yaml".format(*attr))))

    # print out our choices
    print(background, race + ("({})".format(subrace) if subrace != "" else ""), cl + "({})".format(archetype))

    # save class and archetype to character
    character["class"] = cl
    character["archetype"] = archetype

    return character


# generates basic yaml files, should only be used for creating all files
# does not deal with modifiers, proficiencies, or anything above weighting everything the same
def gen_yamls():
    # base path for Data Gen folder
    basepath = "Data/Gen/"
    os.makedirs(basepath, 0o700, True)

    # make a folder for each race
    for race in sorted(races):
        path = basepath
        os.makedirs(path + race, 0o700, True)
        path += race

        subracePath = path
        # make a list of subraces for each race
        with open(path + "/subraces.yaml", "w") as subraces_file:
            subraces = races[race]["subraces"]
            if subraces is None:
                subraces = [""]
            for subrace in subraces:
                path = subracePath
                subraces_file.write("\"{}\":\n  weight: 2\n".format(subrace))
                if subrace:
                    os.makedirs(path + "/" + subrace, 0o700, True)
                    path += "/" + subrace

                classPath = path
                # make a list of classes for each subrace
                with open(path + "/classes.yaml", "w") as classes:
                    path = classPath
                    cl = yaml.load(open("Data/classes.yaml"))
                    for c in sorted(cl):
                        classes.write("\"{}\":\n  weight: 2\n".format(c))
                        os.makedirs(path + "/" + c, 0o700, True)

                        # make a list of archetypes for the class
                        with open(path + "/" + c + "/archetypes.yaml", "w") as archetypes:
                            for archetype in sorted(cl[c]["archetypes"]):
                                archetypes.write("\"{}\":\n  weight: 2\n".format(archetype))

                # make a list of backgrounds for each subrace
                with open(path + "/backgrounds.yaml", "w") as backgrounds:
                    for background in sorted(yaml.load(open("Data/backgrounds.yaml"))):
                        backgrounds.write("\"{}\":\n  weight: 2\n".format(background))


# make a "one pass" character, stats are returned as first rolled, no conditions
def make_character():
    character = create()
    stats = sorted(r.roll_stats(), reverse=True)
    print("stats: {}".format(stats))
    s.assign_stats(character, stats)
    a.add_details(character)
    level_character(character, 1)
    return character


# make a "colville" character, roll stats in order, apply bonuses, determine class
def make_character_coville():
    stats = r.roll_stats_coville()
    character = create(stats)
    level_character(character, 1)
    return character


# create a character where the sum of the modifiers must be at least +5
def make_character_min_mod():
    character = create()
    stats = r.roll_stats_min_mod()
    print("stats: {}".format(stats))
    s.assign_stats(character, stats)
    a.add_details(character)
    level_character(character, 1)
    return character


# create a character with at least one score above 15 and at least one below 8
def make_character_8_15():
    character = create()
    stats = r.roll_stats_8_15()
    print("stats: {}".format(stats))
    s.assign_stats(character, stats)
    a.add_details(character)
    level_character(character, 1)
    return character


# create a character using the standard array
def make_character_standard_array():
    make_character_array([15, 14, 13, 12, 10, 8])


# create a character using the high low standard array
def make_character_standard_array_high_low():
    make_character_array([15, 8] * 3)


# create a character using the all mid standard array
def make_character_standard_array_mid():
    make_character_array([13, 12] * 3)


# make a character given already present stats
def make_character_array(stats):
    character = create()
    print("stats: {}".format(stats))
    s.assign_stats(character, stats)
    a.add_details(character)
    level_character(character, 1)
    return character

# file that gives general leveling info
# right now just xp
levels = yaml.load(open("Data/level.yaml"))


# set level, xp, and proficiency bonus
def level_character(character, level):
    character["level"] = level
    character["xp"] = levels[level]["exp"]
    character["proficiency bonus"] = levels[level]["proficiency_bonus"]

# TODO add rest of data to character

# generate yaml files if they don't exist
if not os.path.exists("Data/Gen"):
    print("Generating yaml files")
    gen_yamls()

character = make_character()

pprint.pprint(character)


# give user the option to save the character for later
keep = input("Keep character? ")

if keep in ("yes", "Yes", "Y", "y"):
    # add character and rewrite file
    with open("characters.json", "a") as characters_file:
        characters_file.write(str(character) + "\n")
