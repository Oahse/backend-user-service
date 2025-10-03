# Backend API Documentation

This document outlines the available API endpoints for the backend service.

## Base URL

The base URL for the API is dependent on your deployment.
- **Development:** `http://localhost:8000/api/v1`
- **Production:** `https://your-domain.com/api/v1` (replace `your-domain.com` with your actual domain)

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

1.  **Obtain a token:**
    *   Send a `POST` request to `/api/v1/auth/login` with `username` (email) and `password`.
    *   The response will contain an `access_token` and `token_type`.
2.  **Include the token in requests:**
    *   For authenticated endpoints, include the `access_token` in the `Authorization` header as `Bearer <access_token>`.

## Endpoints

---

### 1. User Endpoints

#### 1.1. Create User

-   **URL:** `/users/register`
-   **Method:** `POST`
-   **Description:** Registers a new user.
-   **Request Body (JSON):** `schemas.user.UserCreate`
    ```json
    {
      "firstname": "string",
      "lastname": "string",
      "email": "user@example.com",
      "password": "password",
      "role": "Customer",
      "phone": "string",
      "age": 0,
      "gender": "Male"
    }
    ```
-   **Response (JSON):** `schemas.user.UserSchema` (excluding password hash)

#### 1.2. Login User

-   **URL:** `/auth/login`
-   **Method:** `POST`
-   **Description:** Authenticates a user and returns JWT tokens.
-   **Request Body (JSON):** `schemas.user.UserLogin`
    ```json
    {
      "email": "user@example.com",
      "password": "password"
    }
    ```
-   **Response (JSON):**
    ```json
    {
      "access_token": "string",
      "refresh_token": "string",
      "token_type": "bearer"
    }
    ```

#### 1.3. Get Current User

-   **URL:** `/users/me`
-   **Method:** `GET`
-   **Description:** Retrieves the currently authenticated user's profile.
-   **Authentication:** Required (Bearer Token)
-   **Response (JSON):** `schemas.user.UserSchema`

#### 1.4. Update User

-   **URL:** `/users/{user_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing user's profile.
-   **Authentication:** Required (Bearer Token)
-   **Path Parameters:**
    -   `user_id` (UUID): The ID of the user to update.
-   **Request Body (JSON):** `schemas.user.UserUpdate`
-   **Response (JSON):** `schemas.user.UserSchema`

#### 1.5. Delete User

-   **URL:** `/users/{user_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a user.
-   **Authentication:** Required (Bearer Token)
-   **Path Parameters:**
    -   `user_id` (UUID): The ID of the user to delete.
-   **Response:** `204 No Content`

#### 1.6. Manage User Addresses

-   **URL:** `/addresses/`
-   **Method:** `POST`
-   **Description:** Creates a new address for the authenticated user.
-   **Authentication:** Required (Bearer Token)
-   **Request Body (JSON):** `schemas.user.AddressCreate`
-   **Response (JSON):** `schemas.user.AddressSchema`

-   **URL:** `/addresses/{address_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing address for the authenticated user.
-   **Authentication:** Required (Bearer Token)
-   **Path Parameters:**
    -   `address_id` (UUID): The ID of the address to update.
-   **Request Body (JSON):** `schemas.user.AddressUpdate`
-   **Response (JSON):** `schemas.user.AddressSchema`

-   **URL:** `/addresses/{address_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes an address for the authenticated user.
-   **Authentication:** Required (Bearer Token)
-   **Path Parameters:**
    -   `address_id` (UUID): The ID of the address to delete.
-   **Response:** `204 No Content`

---

### 2. Product Endpoints

#### 2.1. Get All Products

-   **URL:** `/products/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all products.
-   **Query Parameters:** `skip` (int), `limit` (int)
-   **Response (JSON):** `List[schemas.products.ProductSchema]`

#### 2.2. Get Product by ID

-   **URL:** `/products/{product_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single product by its ID.
-   **Path Parameters:**
    -   `product_id` (UUID): The ID of the product.
-   **Response (JSON):** `schemas.products.ProductSchema`

#### 2.3. Create Product

-   **URL:** `/products/`
-   **Method:** `POST`
-   **Description:** Creates a new product.
-   **Authentication:** Required (Admin/Manager role)
-   **Request Body (JSON):** `schemas.products.ProductCreate`
-   **Response (JSON):** `schemas.products.ProductSchema`

#### 2.4. Update Product

-   **URL:** `/products/{product_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing product.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `product_id` (UUID): The ID of the product to update.
-   **Request Body (JSON):** `schemas.products.ProductUpdate`
-   **Response (JSON):** `schemas.products.ProductSchema`

#### 2.5. Delete Product

-   **URL:** `/products/{product_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a product.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `product_id` (UUID): The ID of the product to delete.
-   **Response:** `204 No Content`

---

### 3. Category Endpoints

#### 3.1. Get All Categories

-   **URL:** `/categories/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all product categories.
-   **Query Parameters:** `skip` (int), `limit` (int)
-   **Response (JSON):** `List[schemas.category.CategorySchema]`

#### 3.2. Get Category by ID

-   **URL:** `/categories/{category_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single category by its ID.
-   **Path Parameters:**
    -   `category_id` (UUID): The ID of the category.
-   **Response (JSON):** `schemas.category.CategorySchema`

#### 3.3. Create Category

-   **URL:** `/categories/`
-   **Method:** `POST`
-   **Description:** Creates a new category.
-   **Authentication:** Required (Admin/Manager role)
-   **Request Body (JSON):** `schemas.category.CategoryCreate`
-   **Response (JSON):** `schemas.category.CategorySchema`

#### 3.4. Update Category

-   **URL:** `/categories/{category_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing category.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `category_id` (UUID): The ID of the category to update.
-   **Request Body (JSON):** `schemas.category.CategoryUpdate`
-   **Response (JSON):** `schemas.category.CategorySchema`

#### 3.5. Delete Category

-   **URL:** `/categories/{category_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a category.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `category_id` (UUID): The ID of the category to delete.
-   **Response:** `204 No Content`

---

### 4. Tag Endpoints

#### 4.1. Get All Tags

-   **URL:** `/tags/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all product tags.
-   **Query Parameters:** `skip` (int), `limit` (int)
-   **Response (JSON):** `List[schemas.tag.TagSchema]`

#### 4.2. Get Tag by ID

-   **URL:** `/tags/{tag_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single tag by its ID.
-   **Path Parameters:**
    -   `tag_id` (UUID): The ID of the tag.
-   **Response (JSON):** `schemas.tag.TagSchema`

#### 4.3. Create Tag

-   **URL:** `/tags/`
-   **Method:** `POST`
-   **Description:** Creates a new tag.
-   **Authentication:** Required (Admin/Manager role)
-   **Request Body (JSON):** `schemas.tag.TagCreate`
-   **Response (JSON):** `schemas.tag.TagSchema`

#### 4.4. Update Tag

-   **URL:** `/tags/{tag_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing tag.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `tag_id` (UUID): The ID of the tag to update.
-   **Request Body (JSON):** `schemas.tag.TagUpdate`
-   **Response (JSON):** `schemas.tag.TagSchema`

#### 4.5. Delete Tag

-   **URL:** `/tags/{tag_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a tag.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `tag_id` (UUID): The ID of the tag to delete.
-   **Response:** `204 No Content`

---

### 5. Cart Endpoints

#### 5.1. Get User Cart

-   **URL:** `/cart/{user_id}`
-   **Method:** `GET`
-   **Description:** Retrieves the cart for a specific user.
-   **Authentication:** Required (User or Admin role)
-   **Path Parameters:**
    -   `user_id` (UUID): The ID of the user.
-   **Response (JSON):** `schemas.cart.CartSchema`

#### 5.2. Add Item to Cart

-   **URL:** `/cart/items`
-   **Method:** `POST`
-   **Description:** Adds a product variant to the user's cart.
-   **Authentication:** Required (User role)
-   **Request Body (JSON):** `schemas.cart.CartItemCreate`
-   **Response (JSON):** `schemas.cart.CartItemSchema`

#### 5.3. Update Cart Item Quantity

-   **URL:** `/cart/items/{item_id}`
-   **Method:** `PUT`
-   **Description:** Updates the quantity of a specific item in the cart.
-   **Authentication:** Required (User role)
-   **Path Parameters:**
    -   `item_id` (UUID): The ID of the cart item.
-   **Request Body (JSON):** `schemas.cart.CartItemUpdate`
-   **Response (JSON):** `schemas.cart.CartItemSchema`

#### 5.4. Remove Item from Cart

-   **URL:** `/cart/items/{item_id}`
-   **Method:** `DELETE`
-   **Description:** Removes a specific item from the cart.
-   **Authentication:** Required (User role)
-   **Path Parameters:**
    -   `item_id` (UUID): The ID of the cart item to remove.
-   **Response:** `204 No Content`

#### 5.5. Clear Cart

-   **URL:** `/cart/{user_id}/clear`
-   **Method:** `DELETE`
-   **Description:** Clears all items from a user's cart.
-   **Authentication:** Required (User or Admin role)
-   **Path Parameters:**
    -   `user_id` (UUID): The ID of the user whose cart to clear.
-   **Response:** `204 No Content`

---

### 6. Order Endpoints

#### 6.1. Create Order

-   **URL:** `/orders/`
-   **Method:** `POST`
-   **Description:** Creates a new order.
-   **Authentication:** Required (User role)
-   **Request Body (JSON):** `schemas.orders.OrderSchema` (Note: This schema might need adjustment for creation, typically a `OrderCreate` schema is used)
-   **Response (JSON):** `schemas.orders.OrderSchema`

#### 6.2. Get All Orders

-   **URL:** `/orders/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all orders.
-   **Authentication:** Required (Admin/Manager role)
-   **Query Parameters:** `skip` (int), `limit` (int), `user_id` (UUID), `status` (OrderStatus), `start_date` (datetime), `end_date` (datetime)
-   **Response (JSON):** `List[schemas.orders.OrderSchema]`

#### 6.3. Get Order by ID

-   **URL:** `/orders/{order_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single order by its ID.
-   **Authentication:** Required (User or Admin role)
-   **Path Parameters:**
    -   `order_id` (UUID): The ID of the order.
-   **Response (JSON):** `schemas.orders.OrderSchema`

#### 6.4. Update Order Status

-   **URL:** `/orders/{order_id}/status`
-   **Method:** `PUT`
-   **Description:** Updates the status of an order.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `order_id` (UUID): The ID of the order to update.
-   **Request Body (JSON):**
    ```json
    {
      "status": "Processing"
    }
    ```
-   **Response (JSON):** `schemas.orders.OrderSchema`

#### 6.5. Delete Order

-   **URL:** `/orders/{order_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes an order.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `order_id` (UUID): The ID of the order to delete.
-   **Response:** `204 No Content`

---

### 7. Payment Endpoints (Stripe)

#### 7.1. Create Checkout Session

-   **URL:** `/payments/create-checkout-session`
-   **Method:** `POST`
-   **Description:** Creates a Stripe checkout session for a payment.
-   **Authentication:** Required (User role)
-   **Request Body (JSON):**
    ```json
    {
      "order_id": "uuid",
      "amount": 100.00,
      "currency": "usd"
    }
    ```
-   **Response (JSON):**
    ```json
    {
      "id": "cs_test_...",
      "url": "https://checkout.stripe.com/..."
    }
    ```

#### 7.2. Stripe Webhook

-   **URL:** `/payments/webhook`
-   **Method:** `POST`
-   **Description:** Endpoint for Stripe to send webhook events. This endpoint should be publicly accessible and configured in your Stripe dashboard.
-   **Request Body:** Raw Stripe event payload.
-   **Headers:** `Stripe-Signature`
-   **Response (JSON):** `{"status": "success"}`

#### 7.3. Get Payment Status

-   **URL:** `/payments/payment-status/{session_id}`
-   **Method:** `GET`
-   **Description:** Retrieves the status of a Stripe payment session.
-   **Authentication:** Required (User or Admin role)
-   **Path Parameters:**
    -   `session_id` (str): The ID of the Stripe checkout session.
-   **Response (JSON):**
    ```json
    {
      "status": "complete",
      "amount": 100.00,
      "currency": "usd"
    }
    ```

---

### 8. Promocode Endpoints

#### 8.1. Create Promocode

-   **URL:** `/promocodes/`
-   **Method:** `POST`
-   **Description:** Creates a new promocode.
-   **Authentication:** Required (Admin/Manager role)
-   **Request Body (JSON):** `schemas.promocode.PromoCodeCreate`
-   **Response (JSON):** `schemas.promocode.PromoCodeSchema`

#### 8.2. Get Promocode by ID

-   **URL:** `/promocodes/{promocode_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single promocode by its ID.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `promocode_id` (UUID): The ID of the promocode.
-   **Response (JSON):** `schemas.promocode.PromoCodeSchema`

#### 8.3. Update Promocode

-   **URL:** `/promocodes/{promocode_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing promocode.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `promocode_id` (UUID): The ID of the promocode to update.
-   **Request Body (JSON):** `schemas.promocode.PromoCodeUpdate`
-   **Response (JSON):** `schemas.promocode.PromoCodeSchema`

#### 8.4. Delete Promocode

-   **URL:** `/promocodes/{promocode_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a promocode.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `promocode_id` (UUID): The ID of the promocode to delete.
-   **Response:** `204 No Content`

---

### 9. Currency Endpoints

#### 9.1. Get All Currencies

-   **URL:** `/currencies/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all supported currencies.
-   **Query Parameters:** `skip` (int), `limit` (int)
-   **Response (JSON):** `List[schemas.currency.CurrencySchema]`

#### 9.2. Get Currency by ID

-   **URL:** `/currencies/{currency_id}`
-   **Method:** `GET`
-   **Description:** Retrieves a single currency by its ID.
-   **Path Parameters:**
    -   `currency_id` (UUID): The ID of the currency.
-   **Response (JSON):** `schemas.currency.CurrencySchema`

#### 9.3. Create Currency

-   **URL:** `/currencies/`
-   **Method:** `POST`
-   **Description:** Creates a new currency.
-   **Authentication:** Required (Admin/Manager role)
-   **Request Body (JSON):** `schemas.currency.CurrencyCreate`
-   **Response (JSON):** `schemas.currency.CurrencySchema`

#### 9.4. Update Currency

-   **URL:** `/currencies/{currency_id}`
-   **Method:** `PUT`
-   **Description:** Updates an existing currency.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `currency_id` (UUID): The ID of the currency to update.
-   **Request Body (JSON):** `schemas.currency.CurrencyUpdate`
-   **Response (JSON):** `schemas.currency.CurrencySchema`

#### 9.5. Delete Currency

-   **URL:** `/currencies/{currency_id}`
-   **Method:** `DELETE`
-   **Description:** Deletes a currency.
-   **Authentication:** Required (Admin/Manager role)
-   **Path Parameters:**
    -   `currency_id` (UUID): The ID of the currency to delete.
-   **Response:** `204 No Content`
