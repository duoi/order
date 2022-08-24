# NB

You can use this Postman collection https://www.getpostman.com/collections/ea9110a3d29bd3afa71b which, when imported into Postman, should already have the relevant endpoints configured. Just replace the token.

# Setup

1. Clone repo
2. Run `docker-compose build` in the directory, make sure you have docker running
3. Run `docker-compose up` ... it takes a little bit to get going as the app container waits until the db container has fully started before running
4. After migrations have been ran, it begins to populate randomised dummy data, and it should then present you with a username and password to use for authentication
   1. You can create more users and more data by calling `docker exec -it order_web_1 python3 manage.py add_dummy_data`
   2. You can add a custom user with `docker exec -it order_web_1 python3 manage.py add_dummy_data <name>`
   3. You can add `n` number of additional products by adding your `n` at the end, i.e:  `docker exec -it order_web_1 python3 manage.py add_dummy_data 2500`

![image](https://user-images.githubusercontent.com/10301400/186498491-24bd6914-5e51-4b46-b227-fd5ae64783c7.png)

All of the users created here have full superuser privileges for ease of testing - you can log into Django admin etc.

# Authentication

1. Send a `POST` request to `/api/auth/login/` with the body `{"username": <username>, "password": <password>}`
2. This should give you back something to the effect of `Token dfg897s....d8923h` as a response.
3. Add this as an `Authorization` header with the token as the value (including the word `Token` and the space)
   1. It should look something like `Authorization: Token dfg897s....d8923h`

![image](https://user-images.githubusercontent.com/10301400/186498618-32b92fd0-ac63-440f-af2d-ea7448f4a8b7.png)

# API

### Note that a trailing slash `/` is required on all endpoints or the server will say the path doesn't exist

The following are the possible API endpoints related to the ordering workflow:

1. `/api/orders/` > `GET` > Shows all historically placed orders for the logged in user
   1. `/api/orders/cart/` > `GET` > Shows the current incomplete order (i.e active cart)
   2. `/api/orders/update_cart/` > `POST` > takes in a quantity and ID you get from the products endpoint
      1. If the product exists and there is sufficient quantity, it will add it to your cart
      2. If the product is already in your cart it will update the existing quantity
      3. Giving a quantity of `0` will remove the item from your cart
   3. `/api/orders/checkout/` > `POST` > Checks out the current cart; places the current cart as an order
      1. If the items in the cart are out of stock or no longer available in the sufficient quantities, it will update the cart accordingly and prompt to review + perform checkout again
2. `/api/products/` > `GET` > Shows all products regardless of whether they are in or out of stock
   1. This could have been made more fancy but I didn't want to complicate testing when checking to see if inventory is reduced etc

The following are the possible API endpoints related to the login/logout workflow:

1. `/api/auth/login/` > `POST` > Takes in `username` and `password` in the body and returns a valid token
2. `/api/auth/logout/` > `POST` > Invalidates the current token (out of the box from rest-knox)
3. `/api/auth/logoutall/` > `POST` > Invalidates all tokens associated with the logged in user (out of the box from rest-knox)

# Deployment

Looking at this from AWS, it really depends on if we want to use plain EC2 or something like Beanstalk. It's dockerized so I guess we can use profiles to remove the db container on prod deploys and instead connect to an RDS instance. I would use some kind of CI/CD (whatever Bitbucket or Gitlab etc provides) to build and push the image up, and if we're using something like Beanstalk, it would handle bringing down the old servers and bringing up the new ones. We would probably have a more complex start script that would make sure migrations/static assets and everything else is handled.

# Notes

1. I would have liked to add tests -- there is a lot happening with lots of interactions and tests are extremely important to have. But the 4 hour time limit went by quicker than anticipated. I would have used the same factories I used for the dummy data to speed up testing. If this is a requirement, please let me know and I can add tests ASAP.
2. A better way of removing items from the cart -- currently you post `0` as the quantity but this isn't very nice
3. Some sort of self-documenting API add-on like Swagger would have been nice here
4. Optimizations of different parts of the code -- some of it is expensive both in time and query count and can be optimized, however, this was low-priority as it's fairly out of scope for the exercise as far as I see it.
5. I used `rest-knox` to handle the tokens as I'm not a fan of DRFs implementation, knox provides a lot of different features that should probably be upstreamed to DRF core
6. I made the assumption that a person can only have one open cart at any one time, however, I imagine they could have multiple
7. The way the offers were structured revolved around this being a demo exercise. There is a lot of enhancement that can happen on this front if we had multiple offers from different suppliers.
8. Some of the location of some parts of the code (i.e the `add` method on one of the serializers) should probably be moved out, as I refactored several times and that location is probably now inappropriate
9. The way I handled floats and rounding is probably wrong -- I should be ceiling the value instead, but I left it for the exercise. In production we'd probably need to have a chat of how to deal with the rounding of three or more decimal places.
10. We should probably store the currency somewhere as, just within Europe, there are many.
11. Handling of permissions was terribad:
    1. In the viewsets I just did `IsAuthenticated` and limited the queryset in the `get_queryset` methods
    2. This should probably be a custom permission class to check if the object belongs to the user
12. I was initially going to randomly generate images to associate with the products but ran out of time, so the field is still there
13. I was also going to improve the way the random dimensions are generated but also ran out of time
14. I left basic authentication enabled so you can log in via Django Admin and use DRF's browsable API if you didn't want to load up postman (this is also why I made the users superusers)
15. Some things that I'm adding properties/methods for I would have preferred to use database fields for in a production environment -- as it stands the same stuff is calculated over and over, so this can be enhanced
16. Fetching of products and other things can also be moved to redis or something else to avoid the constant DB lookups
17. I named a field `is_confirmed` on the `Order` model but it should probably be named to something a bit clearer
18. Better messages on checkout when there no longer is stock -- telling you which items were changed and how -- would have been good to add, but ran out of time
19. I did a very late refactoring of how products are added to the cart and I'm afraid I didn't have time to test all the edge cases. Unit tests would have been great here if I hadn't ran out of time for that.
20. I've left `DEBUG` mode enabled for the sake of testing.
21. I would have used a more HATEOAS flow of list/detail/action (i.e `/order/34/update_cart/`) in a production environment but for this exercise I started on a few assumptions listed above that probably weren't accurate, i.e, I might considering adding `add_to_cart` functionality directly on the individual products.
