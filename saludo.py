def greet_user(name):
    print(f"Hola, {name}! Bienvenido!")


def main():
    user_name = input("Introduce tu nombre, por favor: ")
    greet_user(user_name)


if __name__ == "__main__":
    main()
