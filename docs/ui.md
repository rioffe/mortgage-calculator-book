# Calculator UI Layout

The current window, as built through Chapter 11.9:

    Principal ($):           [____________]
    Annual rate (e.g. 0.06): [____________]
    Term (years):            [____________]
    Payments per year:       [____________]

    [ Calculate ]  [ Clear ]

    Fixed periodic payment: $1,199.10

    ----------------------------------------

    Ask a question:  [________________________________]  [ Ask ]

    Answer:

## Behavior
- Calculate / Clear: as specified in SPEC.md's Interfaces section.
- Ask: sends the typed question to ask_local (Chapter 11), and
  displays the returned plain-language answer below the field.
  Uses the same MortgageInput / calculate_validated_payment path
  as everything else in this project, by way of the Chapter 10
  tool interface — never a separate calculation.
