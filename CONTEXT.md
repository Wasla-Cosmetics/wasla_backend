# Wasla Store

Wasla's catalog language defines how products, prices, and customer-facing
offers are understood across the storefront.

## Catalog Ownership

**Brand**:
The customer-facing catalog owner. A Brand contains one or more Branches.
_Avoid_: Manufacturer, Store

**Branch**:
A catalog location owned by one Brand, with its own Category hierarchy.
_Avoid_: Outlet, Global branch

**Category**:
A node in one Branch's product hierarchy. A parent Category always belongs to
the same Branch.
_Avoid_: Global category, Branch category

**Product**:
A sellable catalog item assigned to one Category. Its Branch and Brand are
inherited from that Category.
_Avoid_: Branch product, Product listing

**Primary product image**:
The image stored directly on a Product and used as its main storefront image.
_Avoid_: Base image

**Additional product image**:
One of zero or more ProductImage records that form the rest of a Product's
gallery.
_Avoid_: Secondary base image

## Pricing

**Default price**:
The current selling price a customer pays for a product.
_Avoid_: Base price, regular price

**Compare-at price**:
An optional higher reference price displayed alongside the default price to
communicate a reduction.
_Avoid_: Old price, original price

**Discount percentage**:
The reduction from the compare-at price to the default price, expressed as a
percentage. A product without a compare-at price has no discount.
_Avoid_: Stored discount, discount rate

## Localization

**Response language**:
The language selected by `Accept-Language` for translated response fields.
The special value `all` exposes every configured translation on catalog list
and search responses.

**Search language**:
Catalog search and translated filters always inspect every configured
translation. It is independent of the response language.
