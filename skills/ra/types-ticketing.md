# Resident Advisor GraphQL: Ticketing, payment and admin object types
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

Types for ticketing, guestlist, presale, embeddable widgets, HelpScout and payments.

```graphql
type Embeddable_Token {
  embedUrl: String!
  token: ID!
}

type GuestlistDto {
  guests: [GuestDto!]!  # The list of guestlist guests
  total: Float!  # The total number of guestlist guests
}

type Guestlist_ValidationSchemas {
  addGuestlistGuestInput: JSON!  # Validation schema for adding a guestlist guest
}

type HelpScoutBeacon {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  name: String!
  beaconId: String!
  published_at: DateTime
  helpScoutConfigs(sort: String, limit: Int, start: Int, where: JSON): [HelpScoutConfig]
  customFields(sort: String, limit: Int, start: Int, where: JSON): [HelpScoutCustomFields]
}

type HelpScoutBeaconAggregator {
  count: Int
  totalCount: Int
}

type HelpScoutBeaconConnection {
  values: [HelpScoutBeacon]
  groupBy: HelpScoutBeaconGroupBy
  aggregate: HelpScoutBeaconAggregator
}

type HelpScoutBeaconConnectionBeaconId {
  key: String
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconConnectionCreated_at {
  key: DateTime
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconConnectionId {
  key: ID
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconConnectionName {
  key: String
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconConnectionPublished_at {
  key: DateTime
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconConnectionUpdated_at {
  key: DateTime
  connection: HelpScoutBeaconConnection
}

type HelpScoutBeaconGroupBy {
  id: [HelpScoutBeaconConnectionId]
  created_at: [HelpScoutBeaconConnectionCreated_at]
  updated_at: [HelpScoutBeaconConnectionUpdated_at]
  name: [HelpScoutBeaconConnectionName]
  beaconId: [HelpScoutBeaconConnectionBeaconId]
  published_at: [HelpScoutBeaconConnectionPublished_at]
}

type HelpScoutConfig {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  url: String
  screen: String
  helpScoutBeacon: HelpScoutBeacon
  published_at: DateTime
}

type HelpScoutConfigAggregator {
  count: Int
  totalCount: Int
}

type HelpScoutConfigConnection {
  values: [HelpScoutConfig]
  groupBy: HelpScoutConfigGroupBy
  aggregate: HelpScoutConfigAggregator
}

type HelpScoutConfigConnectionCreated_at {
  key: DateTime
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionHelpScoutBeacon {
  key: ID
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionId {
  key: ID
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionPublished_at {
  key: DateTime
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionScreen {
  key: String
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionUpdated_at {
  key: DateTime
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigConnectionUrl {
  key: String
  connection: HelpScoutConfigConnection
}

type HelpScoutConfigGroupBy {
  id: [HelpScoutConfigConnectionId]
  created_at: [HelpScoutConfigConnectionCreated_at]
  updated_at: [HelpScoutConfigConnectionUpdated_at]
  url: [HelpScoutConfigConnectionUrl]
  screen: [HelpScoutConfigConnectionScreen]
  helpScoutBeacon: [HelpScoutConfigConnectionHelpScoutBeacon]
  published_at: [HelpScoutConfigConnectionPublished_at]
}

type HelpScoutCustomFields {
  id: ID!
  created_at: DateTime!
  updated_at: DateTime!
  fieldName: String
  fieldId: Int
  published_at: DateTime
}

type HelpScoutCustomFieldsAggregator {
  count: Int
  totalCount: Int
  sum: HelpScoutCustomFieldsAggregatorSum
  avg: HelpScoutCustomFieldsAggregatorAvg
  min: HelpScoutCustomFieldsAggregatorMin
  max: HelpScoutCustomFieldsAggregatorMax
}

type HelpScoutCustomFieldsAggregatorAvg {
  fieldId: Float
}

type HelpScoutCustomFieldsAggregatorMax {
  fieldId: Float
}

type HelpScoutCustomFieldsAggregatorMin {
  fieldId: Float
}

type HelpScoutCustomFieldsAggregatorSum {
  fieldId: Float
}

type HelpScoutCustomFieldsConnection {
  values: [HelpScoutCustomFields]
  groupBy: HelpScoutCustomFieldsGroupBy
  aggregate: HelpScoutCustomFieldsAggregator
}

type HelpScoutCustomFieldsConnectionCreated_at {
  key: DateTime
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsConnectionFieldId {
  key: Int
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsConnectionFieldName {
  key: String
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsConnectionId {
  key: ID
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsConnectionPublished_at {
  key: DateTime
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsConnectionUpdated_at {
  key: DateTime
  connection: HelpScoutCustomFieldsConnection
}

type HelpScoutCustomFieldsGroupBy {
  id: [HelpScoutCustomFieldsConnectionId]
  created_at: [HelpScoutCustomFieldsConnectionCreated_at]
  updated_at: [HelpScoutCustomFieldsConnectionUpdated_at]
  fieldName: [HelpScoutCustomFieldsConnectionFieldName]
  fieldId: [HelpScoutCustomFieldsConnectionFieldId]
  published_at: [HelpScoutCustomFieldsConnectionPublished_at]
}

type PaymentUser {
  paymentDetails: IPaymentDetails
  promoterId: ID!
  userToken: String!
  transferMethodToken: String
  profileType: ProfileType!
  businessName: String
  address: Address
  dateOfBirth: Date
  firstName: String
  lastName: String
  email: String
}

type Presale {
  eventId: ID!
  id: Float!
  onSaleFrom: DateTime!
  promoCodeId: String!
  scheduledEmailDate: DateTime!
  signedUpUsers: [PresaleUsers!]!
  ticketId: String!
  userCount: Float!
  ticket: Ticket
}

type PresaleUsers {
  eventId: ID!
  id: ID!
  signedUpAt: DateTime!
  userId: ID!
}

type Ticketing_AdminRefundAmounts {
  refundedFeeAmount: Decimal
  refundedRetailAmount: Decimal!
  refundedWholesaleAmount: Decimal!
}

type Ticketing_AggregateOrder {
  _count: Ticketing_OrderCountAggregate  # Count aggregate for orders
}

type Ticketing_AggregateTicketTier {
  _count: Ticketing_TicketTierCountAggregate!
}

type Ticketing_AggregateTicketTierRevisionLogs {
  _count: Ticketing_TicketTierRevisionLogsCountAggregate!
}

type Ticketing_AvailableOrderQuantity {
  maxPerTier: Int!  # Maximum tickets per order
  minPerTier: Int!  # Minimum tickets per order
}

type Ticketing_Barcode {
  barcodeGroup: Ticketing_BarcodeGroup  # The barcode group that the barcode belongs to
  createdAt: DateTime!  # The barcode creation date
  creationReason: String  # Reason for barcode creation
  displayName: String!  # The display name for the customer that the barcode is associated with
  displayTitle: String!  # The display title of the barcode, either the title of the ticket tier or "Guestlist"
  eventBarcodes: [Ticketing_EventBarcodeV2!]!  # relation to the event barcodes
  guestId: String  # The guest ID for the barcode
  id: UUID!  # The barcode id
  invalidatedBarcode: Ticketing_Barcode  # relation to the previous barcode replaced by an upgraded barcode
  invalidationReason: Ticketing_BarcodeInvalidationReason  # Reason why barcode is invalid
  order: Ticketing_Order  # Relation to the order
  orderItem: Ticketing_OrderItem  # Relation to the order item
  orderNumber: String  # The order number for the barcode
  refundStatus: String  # Get barcode refund status
  scans: [Ticketing_Scan!]!  # Scans that have been performed for the barcode
  ticketHolderNameChangeCount: Int!  # The number of ticket holder name changes made for this barcode
  ticketNumber: String!  # The number of the barcode
  ticketTier: Ticketing_TicketTierV2  # Relation to the ticket tier
  type: Ticketing_BarcodeType!  # The type of created barcode
  updatedAt: DateTime!  # The date and time the barcode was updated
  upgradedBarcode: Ticketing_Barcode  # relation to the upgraded barcode
  userId: String  # The id of the owner of the barcode
  valid: Boolean!  # is event barcode valid for scanning
  user: User
}

type Ticketing_BarcodeGroup {
  id: String!  # Get the ID of the barcode group
  scans: Ticketing_TicketScans!  # Get scan statistics for all barcodes in this group
  title: String  # Get the title of the barcode group
  type: Ticketing_BarcodeType  # Get the type of the barcode group
}

type Ticketing_BarcodeGroupChain {
  barcodeGroups: [Ticketing_BarcodeGroup!]!  # Get all barcode group for this barcode group chain
  id: String!  # Get the ID of the barcode group chain
  scans: Ticketing_TicketScans!  # Get scan statistics for all barcodes in this chain
  type: Ticketing_BarcodeType  # Get the type of the barcode group chain
}

type Ticketing_Basket {
  basketItems: [Ticketing_BasketItem!]  # The items in this basket
  createdAt: DateTime!  # The date and time this basket was created
  currency: Ticketing_Currency  # The currency used for this basket
  expiresAt: DateTime!  # The date and time this basket will expire
  id: UUID!
  order: Ticketing_Order  # The order associated with this basket
  retailChannelCode: Ticketing_RetailChannelCodes  # Order retail channel code
  total: Decimal!  # The total cost value of all the items in the basket
  transactionLogs: [Ticketing_TransactionLog!]  # The transaction logs associated with this basket
  updatedAt: DateTime!  # The date and time this basket was last updated
  userId: String
  user: User
}

type Ticketing_BasketItem {
  basket: Ticketing_Basket!
  basketId: UUID!  # The id of the basket this item belongs to
  fee: Decimal  # Admin Event fee
  id: UUID!
  orderItems: [Ticketing_OrderItem!]
  price: Decimal!  # The price of this ticket tier at the time of adding it to the basket
  quantity: Int!  # The quantity of tickets in this basket line item
  resaleQuantity: Int!  # The subset of quantity related to resale for this basket line item
  ticketCost: Ticketing_TicketCost
  ticketPromoId: UUID  # The ticket tier promo that was applied to this basket item
  ticketTier: Ticketing_TicketTier! @deprecated  # Basket item ticketTier
  ticketTierId: UUID!  # The ticket tier this basket item refers to
  ticketTierV2: Ticketing_TicketTierV2!  # Basket item ticketTier
  total: Decimal!  # The total cost of this basket item (quantity * price)
}

type Ticketing_CalculatedTicketCost {
  feeAmount: Decimal!  # Ticket fee amount
  retailPrice: Decimal!  # Retail ticket price
  wholesalePrice: Decimal!  # Wholesale ticket price
}

type Ticketing_Country {
  code: String!  # Unique code of the country ISO 3166-1 alpha-3
  code2: String!  # Unique code of the country ISO 3166-1 alpha-2
  createdAt: DateTime!  # Creation date
  defaultCurrency: Ticketing_Currency  # Default currency of the country
  defaultCurrencyId: UUID!  # Reference to the default currency of the country
  feeDisplayTypes: [Ticketing_FeeDisplayType!]!  # Defines the allowed options for fee display at the country level
  feeSettings: [Ticketing_CountryFeeSettings!]!  # Fee types and percentages for this country
  id: UUID!  # Unique identifier of the country
  title: String!  # Title of the country
  updatedAt: DateTime!  # Last update date
}

type Ticketing_CountryFeeSettings {
  country: Ticketing_Country!  # Country
  countryId: String!  # Country ID
  id: UUID!  # Country fee ID
  percentage: Decimal!  # Fee percentage
  type: Ticketing_FeeType!  # The type of the fee setting
}

type Ticketing_CreateOrderResult {
  action: Ticketing_PaymentAction
  adminRefundAmounts: Ticketing_AdminRefundAmounts!  # Refunded amounts of the order for admin
  amount: Decimal!  # The total cost amount of the order
  barcodes: [Ticketing_Barcode!]  # Order barcodes
  basket: Ticketing_Basket!  # Order basket
  billingName: String  # The name of the person who made the order
  completedAt: DateTime  # The date and time the order was completed
  createdAt: DateTime!  # The date and time the order was created
  currency: Ticketing_Currency!  # Order currency
  displayAmount: Decimal!  # Total amount to display to the customer
  displayFee: Decimal  # Total fees to display to the customer
  events: [Ticketing_Event!]  # List order events
  fulfilmentStatus: Ticketing_FulfilmentStatus!  # The fulfilment status of the order
  id: UUID!  # The id of the order
  notes: [Ticketing_OrderNote!]!  # Order orderNotes
  orderItems: [Ticketing_OrderItem!]  # Order orderItems
  orderNumber: String!  # The number of the order
  orderPaymentMethod: Ticketing_OrderPaymentMethod  # The payment method used
  paymentMethod: String @deprecated  # The payment method used
  paymentPlan: Ticketing_PaymentPlan  # The instalment plan this order is paid through, if any
  paymentProvider: String  # The details of the payment provider used
  paymentUrl: String  # Returns payment url in the payment provider dashboard for the given order
  postcode: String  # The postcode used for payment
  promoterSalesData: Ticketing_OrderPromoterSalesData!  # Get sales amounts for promoter
  refundAmounts: Ticketing_RefundAmounts!  # Refunded amounts of the order
  refundStatus: Ticketing_RefundStatus  # Resolves the overall refund status for the order based on its items
  refunds: [Ticketing_Refund!]  # Order refunds
  retailChannelCode: Ticketing_RetailChannelCodes!  # Order retail channel code
  source: Ticketing_OrderSourceType!  # The platform used to place an order
  status: Ticketing_OrderStatus!  # The status of the order
  transactionLogs: [Ticketing_TransactionLog!]  # Order transaction logs
  transactionUrl: String  # Get transaction URL for payment
  updatedAt: DateTime!  # The date and time the order was last updated
  userId: String!  # The id of order owner
  userMarketingPreferencesLog: Ticketing_UserMarketingPreferencesLog!  # Order userMarketingPreferencesLog
}

type Ticketing_Currency {
  code: String!  # Currency code
  createdAt: DateTime!  # Creation date
  defaultCountries: [Ticketing_Country!]  # Default currency of the country
  events: [Ticketing_Event!]  # Events where currency is used
  id: UUID!  # Currency id
  minFee: Decimal!  # Currency min fee
  paymentPlanFlatFee: Decimal  # Payment plan flat fee set for the currency
  title: String!  # Currency title
  updatedAt: DateTime!  # Last update date
}

type Ticketing_CustomTermsAndConditions {
  id: UUID!  # Unique identifier for the custom terms and conditions
  url: String!  # URL of the custom terms and conditions
}

type Ticketing_DiscountFixedPromoActionOut {
  discountAmount: Decimal!  # Promo discount amount
  id: UUID!  # Promo action id
}

type Ticketing_DiscountPercentagePromoActionOut {
  discountPercentage: Decimal!  # Promo discount percentage
  id: UUID!  # Promo action id
}

type Ticketing_Event {
  aggregateTicketTierRevisionLogs(_count: Ticketing_TicketTierRevisionLogsAggregateArgsCount, ticketTierId: UUID): Ticketing_AggregateTicketTierRevisionLogs  # Aggregate ticket tier revision log counts for this event
  barcodeGroupChains: [Ticketing_BarcodeGroupChain!]  # Event barcode group chains for this event
  basketFlowType: Ticketing_BasketFlowType!  # The basket flow type for the event, which determines how users add tickets to their basket.
  calculateTicketCost(data: Ticketing_CalculateTicketCostInput!): Ticketing_CalculatedTicketCost!  # Calculate ticket cost with applied fee
  canSubscribeToTicketNotifications(promoCodes: [String!]): Boolean! @deprecated  # Check if users can subscribe to ticket notifications for this event
  country: Ticketing_Country!  # Country in which the event is taking place
  currency: Ticketing_Currency!  # Currency that will be used for the event
  customTermsAndConditions: Ticketing_CustomTermsAndConditions  # Custom terms and conditions for the event
  feeDisplayType: Ticketing_FeeDisplayType  # Fee display type for this event
  feeSetting: Ticketing_FeeSetting  # Fee setting that will be used for the event
  feeType: Ticketing_FeeType  # Fee type for this event
  hasPromotionEnded(promoCodes: [String!]): Boolean!  # Check if the promotion has ended (true if code is inactive or allocation exceeded)
  id: UUID!  # Unique identifier for the event
  importedBarcodes(outlet: String, skip: Int, take: Int = 50): Ticketing_ImportedBarcodesResult!  # A page of imported external barcodes for this event
  importedOutlets: [Ticketing_ImportedOutlet!]!  # The outlets that barcodes were imported from for this event
  inviteGroups: [Ticketing_InviteGroup!]  # Invite groups of the event
  isAnyTicketTierAvailable(promoCodes: [String!] = []): Boolean!  # Check if any ticket tiers are available for this event
  legacyId: String!  # Unique identifier for the event from the existing RA API
  orderQuantity: Ticketing_EventOrderQuantity  # Order quantity min/max limitations set for the event
  paymentPlanOptions: [Ticketing_PaymentPlanOption!]!  # Payment plan options eligible for this event
  pins: [Ticketing_Pin!]  # Active pins for this event
  preConfiguredTicketTitles: [String!]!  # Get pre-configured titles by eventId
  promos: [Ticketing_Promo!]  # Promos of the event
  promoter: Ticketing_UserV2!  # Promoter who is managing the event
  promoterSalesData: Ticketing_EventPromoterSalesData!  # Get sales amounts for promoter
  tags: [Ticketing_EventTag!]!  # Computed display tags for the event
  ticketAllocation: Ticketing_TicketAllocation!  # Get allocation statistics for all tiers in this event
  ticketChains: [Ticketing_TicketChain!]!  # Chains of tickets as defined by sales period dependencies
  ticketListingItems(promoCodes: [String!]! = []): [Ticketing_TicketListingItem!]!  # Ticket listing items containing both ticket groups and ungrouped ticket tiers
  ticketNotificationSubscriptionAvailability(promoCodes: [String!]): Ticketing_TicketNotificationSubscriptionAvailability!  # The type of ticket notification a user can subscribe to for this event (NONE if unavailable)
  ticketScans(where: Ticketing_TicketScansWhereInput): Ticketing_TicketScans  # Get scan statistics for all tiers in this event
  ticketStatus: Ticketing_EventTicketStatus!  # Status of the event, used to determine whether or not tickets can be purchased
  ticketTierRevisionLogs(skip: Int, take: Int = 10, ticketTierId: UUID): [Ticketing_TicketTierRevisionLog!]  # Revision history of ticket tier changes for this event
  ticketTiers: [Ticketing_TicketTier!] @deprecated  # Ticket tiers for the event
  ticketTiersV2(promoCodes: [String!]! = [], queryType: Ticketing_TicketTiersQueryType): [Ticketing_TicketTierV2!]!  # V2 Ticket tiers of the event
  validTicketModels: [Ticketing_TicketModel!]  # Ticket models that are valid for the event
  legacy: Event
}

type Ticketing_EventBarcodeV2 {
  barcode: Ticketing_Barcode!  # The active barcode
  createdAt: DateTime!  # The time event barcode was created
  deviceId: String  # The device that was used to scan the code
  event: Ticketing_Event!  # The event of the event barcode
  id: ID!  # The unique identifier of the event barcode
  orderItem: Ticketing_OrderItem!  # The order item of event barcode
  rejectedAt: DateTime  # Date when the event barcode was rejected
  scanStatus: Ticketing_ScanStatus!  # Scan status of the event barcode
  scannedAt: DateTime  # Date when the event barcode was scanned
  scans: [Ticketing_Scan!]!  # Scans processed on the event barcode
  updatedAt: DateTime!  # The time event barcode was updated
}

type Ticketing_EventOrderQuantity {
  createdAt: DateTime!  # The date and time that this record was created
  event: Ticketing_Event!  # The event this order quantity belongs to
  eventId: UUID!  # The id of the event that this order quantity applies to
  id: UUID!  # Event order quantity ID
  maxPerEvent: Int!  # The maximum number of tickets that can be purchased for this event
  maxPerTier: Int!  # The maximum number of tickets that can be purchased per tier
  minPerEvent: Int!  # The minimum number of tickets that can be purchased for this event
  minPerTier: Int!  # The minimum number of tickets that can be purchased per tier
  updatedAt: DateTime!  # The date and time that this record was last updated
}

type Ticketing_EventPromoterSalesData {
  additionalRevenueFromResale: Decimal!  # Additional revenue generated from resale purchases
  fullyRefundedTicketsCount: Int!  # Get amount of tickets with fully refunded wholesale amount
  grossLiability: Decimal!  # Promoter liability increased calculated by the sum of all purchases from itemised book keeping
  hasTransactionData: Boolean!  # Check if the promoter has any transaction data
  liabilityReduced: Decimal!  # Promoter liability reduced calculated as sum of all transaction reversals from the itemised bookkeeping
  netLiability: Decimal!  # The actual amount promoter gets from sold tickets (including refunds) calculated as sum of all transaction minus transac
  refundsDisplayCount: Int!  # Count of invalidated paid barcodes due to refund or manual invalidation
  ticketsInResaleQueue: Int!  # Number of tickets currently listed on the resale queue
  ticketsResold: Int!  # Total number of tickets resold across all ticket tiers for the event
  totalPossibleRevenue: Decimal!  # Total possible revenue from tickets sales
  validPaidTicketsDisplayCount: Int!  # Count of valid paid barcodes for the event
}

type Ticketing_EventTag {
  defaultTitle: String!  # English fallback title, shown when the client has no translation for the type
  type: Ticketing_EventTagType!  # Stable tag type, mapped by clients to a translation
}

type Ticketing_FeeSetting {
  id: UUID!
  percentage: Decimal!  # The percentage of the fee
  type: Ticketing_FeeType!  # The type of fee setting
}

type Ticketing_GlobalSetting {
  createdAt: DateTime!  # Creation date
  id: UUID!  # Global setting id
  name: Ticketing_GlobalSettingsNameType!  # Global setting name
  updatedAt: DateTime!  # Last update date
  value: String!  # Global setting value
}

type Ticketing_HiddenPromoActionOut {
  id: UUID!
}

type Ticketing_ImportedBarcode {
  displayName: String!  # The display name for the ticket holder of the barcode
  displayScanStatus: String!  # Readable scan status of the barcode
  displayTitle: String!  # The ticket title the barcode was imported with
  id: UUID!  # Unique identifier for the barcode
  outlet: String!  # The outlet the barcode was imported from
  scanStatus: Ticketing_ScanStatus!  # Scan status of the barcode
  ticketNumber: String!  # The number of the barcode
  valid: Boolean!  # Whether the barcode is valid for scanning
}

type Ticketing_ImportedBarcodesResult {
  items: [Ticketing_ImportedBarcode!]!  # The imported barcodes for the requested page
  scannedCount: Int!  # Number of matching imported barcodes that have been scanned, regardless of pagination
  total: Int!  # Total number of matching imported barcodes for the event, regardless of pagination
  unscannedCount: Int!  # Number of matching imported barcodes that have not been scanned, regardless of pagination
}

type Ticketing_ImportedOutlet {
  count: Int!  # The number of barcodes imported from this outlet
  name: String!  # The name of the outlet the barcodes were imported from
  scannedCount: Int!  # Number of imported barcodes that have been scanned for this outlet
  unscannedCount: Int!  # Number of imported barcodes that have not been scanned for this outlet
}

type Ticketing_InvalidateImportedBarcodesResult {
  invalidatedCount: Int!  # The number of imported barcodes that were invalidated
}

type Ticketing_InviteGroup {
  discountPercentage: Decimal!  # Discount percentage applied by invites in this group
  id: UUID!
  inviteCount: Int!  # Number of invites in this group
  name: String!  # Display name of the group
  ticketTierIds: [UUID!]!  # Ticket tiers the invites in this group apply to
}

type Ticketing_MerchantSession {
  merchantSession: JSON!  # Merchant session
}

type Ticketing_Order {
  adminRefundAmounts: Ticketing_AdminRefundAmounts!  # Refunded amounts of the order for admin
  amount: Decimal!  # The total cost amount of the order
  barcodes: [Ticketing_Barcode!]  # Order barcodes
  basket: Ticketing_Basket!  # Order basket
  billingName: String  # The name of the person who made the order
  completedAt: DateTime  # The date and time the order was completed
  createdAt: DateTime!  # The date and time the order was created
  currency: Ticketing_Currency!  # Order currency
  displayAmount: Decimal!  # Total amount to display to the customer
  displayFee: Decimal  # Total fees to display to the customer
  events: [Ticketing_Event!]  # List order events
  fulfilmentStatus: Ticketing_FulfilmentStatus!  # The fulfilment status of the order
  id: UUID!  # The id of the order
  notes: [Ticketing_OrderNote!]!  # Order orderNotes
  orderItems: [Ticketing_OrderItem!]  # Order orderItems
  orderNumber: String!  # The number of the order
  orderPaymentMethod: Ticketing_OrderPaymentMethod  # The payment method used
  paymentMethod: String @deprecated  # The payment method used
  paymentPlan: Ticketing_PaymentPlan  # The instalment plan this order is paid through, if any
  paymentProvider: String  # The details of the payment provider used
  paymentUrl: String  # Returns payment url in the payment provider dashboard for the given order
  postcode: String  # The postcode used for payment
  promoterSalesData: Ticketing_OrderPromoterSalesData!  # Get sales amounts for promoter
  refundAmounts: Ticketing_RefundAmounts!  # Refunded amounts of the order
  refundStatus: Ticketing_RefundStatus  # Resolves the overall refund status for the order based on its items
  refunds: [Ticketing_Refund!]  # Order refunds
  retailChannelCode: Ticketing_RetailChannelCodes!  # Order retail channel code
  source: Ticketing_OrderSourceType!  # The platform used to place an order
  status: Ticketing_OrderStatus!  # The status of the order
  transactionLogs: [Ticketing_TransactionLog!]  # Order transaction logs
  transactionUrl: String  # Get transaction URL for payment
  updatedAt: DateTime!  # The date and time the order was last updated
  userId: String!  # The id of order owner
  userMarketingPreferencesLog: Ticketing_UserMarketingPreferencesLog!  # Order userMarketingPreferencesLog
  user: User
}

type Ticketing_OrderCountAggregate {
  _all: Int!  # Total count of all orders
}

type Ticketing_OrderEventPromoterSalesData {
  completedAtDaysBeforeEventStart: Int  # Get number of days from order completion to event start
  eventId: String!  # Get event ID
  orderItemsCount: Int  # Get count of order items per event in order
  title: String!  # Get event title
}

type Ticketing_OrderItem {
  adminRefundAmounts: Ticketing_AdminRefundAmounts  # Refunded amounts of the order item for admin
  allBarcodes: [Ticketing_Barcode!]!  # Order item allBarcodes
  basketItem: Ticketing_BasketItem!  # Order item basketItem
  basketItemId: UUID!  # Order item basketItemId
  displayAmount: Decimal  # Order item amount to display to the customer
  displayFee: Decimal  # Order item fee to display to the customer
  eventBarcodes: [Ticketing_EventBarcodeV2!]!  # Active event barcodes fo the order item
  feeAmount: Decimal!  # Order item fee amount
  id: UUID!  # Order item id
  isRefundable: Boolean!  # Whether a refund can be created for the order item
  isResaleEnabled: Boolean!  # Whether a resale item can be created or deleted for the order item
  order: Ticketing_Order!  # Order item order
  orderId: UUID!  # Order item orderId
  promo: Ticketing_Promo  # Promos used in the order
  refundAmounts: Ticketing_RefundAmounts!  # Refunded amounts of the order item
  refundItems: [Ticketing_RefundItem!]!  # Order item refundItems
  refundStatus: Ticketing_RefundStatus  # The refund status of order item
  resaleItem: Ticketing_ResaleItem  # Resale item associated with this order item, if any
  retailAmount: Decimal!  # Order item retail amount
  ticketTier: Ticketing_TicketTierV2!  # Order item ticketTier
  ticketTierId: UUID!  # Order item ticketTierId
}

type Ticketing_OrderNote {
  content: String!  # Note content
  createdAt: DateTime!  # Note creation date
  id: UUID!  # Note ID
  order: Ticketing_Order  # Related order
  updatedAt: DateTime!  # Note last update date
  userId: String!  # UserId
  user: User
}

type Ticketing_OrderPromoterSalesData {
  eventsData: [Ticketing_OrderEventPromoterSalesData!]  # Get order data per each event in order
  fullyRefundedTicketsCount: Int!  # Amount of tickets with fully refunded wholesale amount
  orderItemsCount: Int  # Get a number of order items in the order
  scansData: [Ticketing_PromoterScansData!]  # Get amounts of scanned tickets in order
}

type Ticketing_PayPalOrder {
  payPalOrderId: String!  # PayPal order ID
  redirectUrl: String!  # PayPal redirect URL
}

type Ticketing_PaymentAction {
  data: JSON!
  paymentId: String!
  type: String!
}

type Ticketing_PaymentPlan {
  createdAt: DateTime!  # The date and time this payment plan was created
  id: UUID!
  status: Ticketing_PaymentPlanStatus!  # The current status of the payment plan
  updatedAt: DateTime!  # The date and time this payment plan was last updated
}

type Ticketing_PaymentPlanCheckout {
  customerId: String!  # The Chargebee customer id for the current user
  paymentIntent: String!  # The Chargebee payment intent id for the basket's total
}

type Ticketing_PaymentPlanOption {
  id: ID!  # The Chargebee scheme id for this option
  numberOfInstalments: Int!  # The number of instalments, including the deposit collected today
  period: Int!  # The number of period units between instalments
  periodUnit: Ticketing_PaymentPlanPeriodUnit!  # The unit of time between instalments
}

type Ticketing_Pin {
  code: String!  # The pin code
  createdAt: DateTime!  # When the pin was created
  event: Ticketing_Event!  # The event this pin is related to
  expiry: DateTime!  # When the pin expires
  id: UUID!  # The pin id
  status: Ticketing_PinStatus!  # Whether the pin is valid or expired
  updatedAt: DateTime!  # When the pin was last updated
}

type Ticketing_PinEvent {
  code: String!
  eventId: String!
  expiry: DateTime!
}

type Ticketing_Promo {
  action: Ticketing_TicketPromoAction!  # The action of the promo
  allocation: Ticketing_PromoAllocation  # Ticket promo allocation
  code: String!  # Promo code
  createdAt: DateTime!  # The date and time that this promo was created
  distributionType: Ticketing_TicketPromoDistributionType!  # How the promo is distributed: a shared promo code or a single-use invite
  hasBeenUsed: Boolean!  # Whether this promo has been used
  id: UUID!  # Promo ID
  isActive: Boolean!  # Whether the promo is active
  ordersCompletedCount: Int!  # Count of completed orders that used this promo
  ticketTierIds: [UUID!]!  # Ticket tier IDs associated with this promo
  ticketTiers: [Ticketing_TicketTier!]!  # Ticket tiers associated with this promo
  type: Ticketing_TicketPromoActionType!  # Type of the promo action
  updatedAt: DateTime!  # The date and time that this promo was updated
  url: String!  # Promo URL
}

type Ticketing_PromoAllocation {
  allocationCount: Int!  # Allocation count
  heldCount: Int!  # Number of times promo has been used in current baskets
  id: String!  # Promo allocation id
  soldCount: Int!  # Number of times promo has been used in completed baskets
}

type Ticketing_Promoter {
  id: ID!
}

type Ticketing_PromoterFeeDisplayTypes {
  feeDisplayTypes: [Ticketing_FeeDisplayType!]!  # Fee display types set for the promoter
  id: UUID!  # Promoter fee display types id
}

type Ticketing_PromoterFeeSettings {
  id: UUID!  # The id of the promoter for which to apply this fee
  percentage: Decimal!  # The percentage of the fee to apply
  promoter: Ticketing_Promoter  # The id of the promoter for which to apply this fee
  type: Ticketing_FeeType!  # The type of fee to apply
}

type Ticketing_PromoterScansData {
  rejected: Int!  # Amount of days rounded to the nearest integer from order complete date to event start date
  scanned: Int!  # Amount of days rounded to the nearest integer from order complete date to event start date
}

type Ticketing_PromoterSetting {
  createdAt: DateTime!  # Creation date
  id: String!  # Promoter setting id
  name: Ticketing_PromoterSettingsNameType!  # Promoter setting name
  promoterId: String!  # Promoter id
  updatedAt: DateTime!  # Last update date
  value: String!  # Promoter setting value
}

type Ticketing_Refund {
  amount: Decimal!  # Refund amount
  createdAt: DateTime!  # Created at
  feeAmount: Decimal!  # Fee amount
  id: UUID!  # Refund ID
  order: Ticketing_Order  # Refund order
  refundItems: [Ticketing_RefundItem!]!  # Refund refundItems
  source: Ticketing_RefundSource!  # Refund source
  transactionUrl: String  # Get transaction URL for refund
  updatedAt: DateTime!  # Updated at
  userId: String  # User ID
  user: User
}

type Ticketing_RefundAmounts {
  refundedFeeAmount: Decimal
  refundedRetailAmount: Decimal!
}

type Ticketing_RefundItem {
  amount: Decimal!  # Refund item amount
  createdAt: DateTime!  # Created at
  feeAmount: Decimal!  # Fee amount
  id: UUID!  # Refund item ID
  orderItem: Ticketing_OrderItem!  # Order item
  orderItemId: UUID!  # Order item ID
  refund: Ticketing_Refund!  # Refund
  refundId: UUID!  # Refund ID
  updatedAt: DateTime!  # Updated at
}

type Ticketing_ResaleItem {
  id: UUID!  # The id of the resale item
  status: Ticketing_ResaleStatus!  # The status of the resale item
}

type Ticketing_SavedCard {
  cardDetails: Ticketing_SavedCardDetails  # Card details
  cardToken: String!
  createdAt: DateTime!
  id: ID!
  isDefaultCard: Boolean!  # Indicates whether this SavedCard is the default one for this user
  postcode: String!
  updatedAt: DateTime!
}

type Ticketing_SavedCardDetails {
  cardBrand: String
  expiryDate: String!
  nameOnCard: String!
  pan: String!
}

type Ticketing_Scan {
  action: Ticketing_ScanAction!  # The action of the scan
  actionTimestamp: DateTime!  # The date and time the action was performed on the device. This is used for conflict resolution.
  barcode: Ticketing_Barcode  # The barcode that was scanned
  createdAt: DateTime!  # The date and time the scan record was created
  deviceId: String  # The device that was used to scan the code
  event: Ticketing_Event  # The event the scan record belongs to
  id: UUID!  # The unique identifier of the scan
  result: Ticketing_ScanResult!  # The result of the scan
  updatedAt: DateTime!  # The date and time the scan record was last updated
}

type Ticketing_ScanAcknowledgement {
  error: Ticketing_ScanError  # Error information if the append failed
  id: UUID  # The id of the persisted scan, null if persistence failed
  ticketNumber: String!  # The ticket number this acknowledgement corresponds to
}

type Ticketing_ScanError {
  error: String!  # The error type or identifier
  message: String!  # The error message
  statusCode: Int!  # The HTTP status code of the error
  ticketNumber: String!  # The ticket number associated with the error
}

type Ticketing_ScannerBarcode {
  barcodeGroupId: ID!
  barcodeId: ID!
  displayName: String!
  displayTitle: String!
  eventId: String!
  importedOutlet: String
  invalidationReason: Ticketing_BarcodeInvalidationReason
  orderNumber: String
  rejectedAt: DateTime
  scanStatus: Ticketing_ScanStatus!
  scannedAt: DateTime
  ticketNumber: String!
  valid: Boolean!
}

type Ticketing_TicketAllocation {
  allocation: Int!  # Total allocated number of tickets
  available: Int!  # Available tickets
  held: Int!  # Tickets currently held in baskets
  sold: Int!  # Sold tickets
}

type Ticketing_TicketCategory {
  displayOrder: Int!
  id: UUID!
  name: String!
}

type Ticketing_TicketChain {
  id: UUID!
  ticketTiers: [Ticketing_TicketTier!]! @deprecated  # Ticket chain ticket tiers
  ticketTiersV2(promoCodes: [String!]! = [], queryType: Ticketing_TicketTiersQueryType): [Ticketing_TicketTierV2!]!  # Ticket chain ticket tiers
}

type Ticketing_TicketChainItem {
  id: ID!
  next: Ticketing_TicketChainItem  # Next item in the ticket chain
  previous: Ticketing_TicketChainItem  # Previous item in the ticket chain
  previousId: ID
  ticketChainId: ID
  ticketTier: Ticketing_TicketTier!  # Ticket tier linked to the ticket chain item
  ticketTierId: ID
}

type Ticketing_TicketCost {
  displayFee: Decimal  # Get the ticket display fee
  displayPrice: Decimal  # Get the ticket display price
  displayPromoFee: Decimal  # Get the display fee with a promo discount
  displayPromoPrice: Decimal  # Get the ticket display price with a promo discount
  fee: Decimal  # Get actual fee
  id: UUID!
  retailPrice: Decimal!  # The retail price of this ticket tier
  ticketTier: Ticketing_TicketTier!  # The ticket tier that this cost belongs to
  ticketTierId: UUID!  # The id of the ticket tier that this cost belongs to
  type: Ticketing_TicketCostType!  # The type of cost
  wholesalePrice: Decimal!  # Get wholesale price of the ticket tier
}

type Ticketing_TicketGroup {
  description: String
  id: UUID!
  image: Ticketing_TicketImage  # Image associated with this ticket group
  name: String!
  ticketCategory: Ticketing_TicketCategory  # Top-level category this ticket group belongs to
  ticketSubCategory: Ticketing_TicketSubCategory  # Sub-category this ticket group belongs to. Nullable if the ticket group does not belong to any category, or belongs to a
  ticketTiers(promoCodes: [String!]! = []): [Ticketing_TicketTierV2!]!  # Ticket tiers in this ticket group
}

type Ticketing_TicketImage {
  alt: String
  id: UUID!
  imageUrl: String!  # Publicly accessible URL of the image
}

type Ticketing_TicketModel {
  baseTicketTier: Ticketing_TicketTier  # The base ticket tier for this ticket model
  createdAt: DateTime!  # The date and time the ticket model was created
  id: UUID!
  type: Ticketing_TicketModelType!  # The type of ticket model
  updatedAt: DateTime!  # The date and time the ticket model was last updated
  validEvents: [Ticketing_Event!]  # The events that this ticket model is valid for
}

type Ticketing_TicketOrderQuantity {
  createdAt: DateTime!  # The date and time that this record was created
  id: UUID!  # Ticket order quantity ID
  maxPerTier: Int!  # The maximum number of tickets that can be ordered for this ticket tier
  minPerTier: Int!  # The minimum number of tickets that can be ordered for this ticket tier
  updatedAt: DateTime!  # The date and time that this record was updated
}

type Ticketing_TicketSalesPeriod {
  createdAt: DateTime!  # The date and time the ticket sales period was created
  endDate: DateTime  # The date and time ticket sales for this period should end
  id: UUID!
  startDate: DateTime  # The date and time ticket sales for this period should start
  ticketTier: Ticketing_TicketTier!  # The ticket tier that this ticket sales period belongs to
  ticketTierId: UUID!  # The id of the ticket tier that this ticket sales period belongs to
  timeZone: TimeZone!  # The time zone that the start and end dates are in
  updatedAt: DateTime!  # The date and time the ticket sales period was last updated
}

type Ticketing_TicketScans {
  rejected: Int!  # Rejected tickets
  scanned: Int!  # Scanned tickets
  unscanned: Int  # Unscanned tickets (can be null if scannedAt is provided)
}

type Ticketing_TicketStep {
  description: String
  id: UUID!
  name: String!
  ticketGroups(promoCodes: [String!]! = []): [Ticketing_TicketGroup!]!  # Ticket groups in this step that have available tickets
}

type Ticketing_TicketSubCategory {
  displayOrder: Int!
  id: UUID!
  name: String!
}

type Ticketing_TicketTier {
  approvalStatus: Ticketing_TicketTierApprovalStatus!  # The approval status of the ticket tier
  availableForPurchase: Boolean!  # Shows if the ticket tier is available for purchase
  barcodes: [Ticketing_Barcode!]
  basketItems: [Ticketing_BasketItem!]
  createdAt: DateTime!  # The time at which the ticket tier was created
  currency: Ticketing_Currency  # Ticket tier currency
  dependentTicketModels: [Ticketing_TicketModel!]  # Ticket tier dependent ticket model
  description: String  # The description of the ticket tier
  event: Ticketing_Event!  # Ticket tier event
  feeSettings: Ticketing_TicketTierFee  # Ticket tier fee
  id: UUID!  # The id of the ticket tier
  inactivityReason: Ticketing_TicketTierInactivityReason  # The active status of the ticket tier
  orderItems: [Ticketing_OrderItem!]  # Ticket tier order items
  orderQuantity: Ticketing_TicketOrderQuantity  # Ticket order quantity
  promoterSalesData: Ticketing_TicketTierPromoterSalesData!  # Get sales amounts for promoter
  ticketAllocation: Ticketing_TicketAllocation  # Get allocation statistics for ticket tier
  ticketCost(promoCodes: [String!]): Ticketing_TicketCost  # Price values of the ticket tier
  ticketModel: Ticketing_TicketModel!  # Ticket tier ticketModel
  ticketNameType: Ticketing_TicketNameType  # Get the name type of the ticket tier
  ticketSalesPeriod: Ticketing_TicketSalesPeriod  # Ticket sales period
  ticketTierPrice: Ticketing_TicketTierPrice! @deprecated  # Get price of ticket tier
  title: String!  # The title of the ticket tier
  updatedAt: DateTime!  # The time at which the ticket tier was last updated
  visible: Boolean!  # Whether the ticket tier is visible to the public
}

type Ticketing_TicketTierCountAggregate {
  _all: Int!
}

type Ticketing_TicketTierFee {
  createdAt: DateTime!  # The date and time when this fee setting was created
  id: UUID!  # Ticket tier fee ID
  isCustomMinFee: Boolean!  # Indicates if the fee has custom minFee value
  isCustomPercentage: Boolean!  # Indicates if the fee has custom percentage value
  minFee: Decimal!  # Min value of Fee
  percentage: Decimal!  # The percentage of the fee
  type: Ticketing_FeeType!  # The type of fee setting
  updatedAt: DateTime!  # The date and time when this fee setting was last updated
}

type Ticketing_TicketTierPrice {
  currency: Ticketing_Currency!  # The currency associated with the ticket tier price
  price: Decimal
}

type Ticketing_TicketTierPromoterSalesData {
  additionalRevenueFromResale: Decimal!  # The additional revenue generated from tickets that have been resold
  fullyRefundedTicketsCount: Int!  # Get amount of tickets with fully refunded wholesale amount
  grossLiability: Decimal!  # Promoter liability increased calculated by the sum of all purchases from itemised book keeping
  liabilityReduced: Decimal!  # Promoter liability reduced calculated as sum of all transaction reversals from the itemised bookkeeping
  netLiability: Decimal!  # The actual amount promoter gets from sold tickets (including refunds) calculated as sum of all transaction minus transac
  refundsDisplayCount: Int!  # Count of invalidated paid barcodes due to refund or manual invalidation
  ticketsInResaleQueue: Int!  # Count of tickets in the tier that are in the resale queue
  ticketsResold: Int!  # Count of tickets that have been resold from the ticket tier
  validPaidTicketsDisplayCount: Int!  # Count of valid paid barcodes for the ticket tier
}

type Ticketing_TicketTierRevisionLog {
  revisionDate: DateTime!  # The time at which the change was made
  revisionItems: [Ticketing_TicketTierRevisionLogItem!]!  # The individual field changes made in this revision
  ticketTierId: UUID!  # The id of the ticket tier that was changed
  ticketTierTitle: String!  # The title of the ticket tier that was changed
  userId: String!  # The id of the user who made the change
  userName: String  # The username of the user who made the change, null for automated changes
}

type Ticketing_TicketTierRevisionLogItem {
  newValue: String  # The value of the field after the change
  previousValue: String  # The value of the field before the change
  type: Ticketing_TicketTierRevisionLogType!  # The field that was changed
}

type Ticketing_TicketTierRevisionLogsCountAggregate {
  _all: Int!
}

type Ticketing_TicketTierSaleStatus {
  hidden: Boolean!  # Shows whether the ticket tier is hidden
  name: Ticketing_TicketTierSaleStatusName!
  soldOut: Boolean!
}

type Ticketing_TicketTierV2 {
  approvalSource: Ticketing_TicketTierApprovalSource  # The source of the approval for the ticket tier
  approvalStatus: Ticketing_TicketTierApprovalStatus!  # The approval status of the ticket tier
  approvalStatusUpdatedAt: DateTime  # The time at which the ticket tier approval status was last updated
  approvalStatusUpdatedBy: String  # The ID of the admin staff who updated the ticket tier approval status
  approvalStatusUpdatedByUsername: String  # The username of the admin staff who updated the ticket tier approval status
  availableForPurchase: Boolean! @deprecated  # Shows if the ticket tier is available for purchase
  availableOrderQuantity: Ticketing_AvailableOrderQuantity!  # Get the available order quantity for the ticket tier.
  availablePreviousTicketTiers: [Ticketing_TicketTierV2!]!  # Ticket tiers from the same event that can be set as the previous ticket chain item. Excludes rejected tiers and tiers al
  createdAt: DateTime!  # The time at which the ticket tier was created
  currency: Ticketing_Currency  # Ticket tier currency
  dependentTicketModels: [Ticketing_TicketModel!]!  # Ticket tier dependent ticket model
  description: String  # The description of the ticket tier
  displayStatus: Ticketing_TicketTierDisplayStatus  # Status that determines how a ticket tier is displayed to buyers. If null, ticket should not be displayed.
  event: Ticketing_Event!  # Ticket tier event
  feeSettings: Ticketing_TicketTierFee  # Ticket tier fee
  id: UUID!  # The id of the ticket tier
  inactivityReason: Ticketing_TicketTierInactivityReason  # The active status of the ticket tier
  orderItems: [Ticketing_OrderItem!]!  # Ticket tier order items
  orderQuantity: Ticketing_TicketOrderQuantity  # Ticket order quantity
  promoterSalesData: Ticketing_TicketTierPromoterSalesData!  # Get sales amounts for promoter
  saleStatus: Ticketing_TicketTierSaleStatus!  # Get status of ticket tier
  ticketAllocation: Ticketing_TicketAllocation!  # Get allocation statistics for ticket tier
  ticketChainItem: Ticketing_TicketChainItem  # Ticket chain item associated with this ticket tier
  ticketCost(promoCodes: [String!]): Ticketing_TicketCost  # Price values of the ticket tier
  ticketModel: Ticketing_TicketModel!  # Ticket tier ticketModel
  ticketNameType: Ticketing_TicketNameType  # Get the name type of the ticket tier
  ticketSalesPeriod: Ticketing_TicketSalesPeriod  # Ticket sales period
  title: String!  # The title of the ticket tier
  updatedAt: DateTime!  # The time at which the ticket tier was last updated
  visible: Boolean!  # Whether the ticket tier is visible to the public
}

type Ticketing_TransactionLog {
  basket: Ticketing_Basket  # This will be set by the app
  basketId: UUID  # This will be set by the app
  createdAt: DateTime!  # This will be set automatically by Prisma
  details: JSON!  # This will be set by the app
  id: UUID!  # This will be an id generated by the app
  order: Ticketing_Order  # This will be set by the app
  orderId: UUID  # This will be set by the app
  type: Ticketing_TransactionLogType!  # Type of the transaction log
  updatedAt: DateTime!  # This will be set automatically by Prisma
  userId: String  # This will be set by the app
  user: User
}

type Ticketing_UserMarketingPreferencesLog {
  id: UUID!  # User marketing preferences log ID
  order: Ticketing_Order  # Related order
  subscribedToPromoterIds: String!  # The ids of the promoters the buyer has subscribed to during the checkout flow for this order
  useRaNewsletter: Boolean!  # The buyer has subscribed to RA Newsletter
}

type Ticketing_UserV2 {
  id: String!  # A unique id of the user
  order(where: Ticketing_OrderIdOrNumberWhereInput!): Ticketing_Order  # Get user order
  orders(eventId: String, orderBy: [Ticketing_OrderOrderByWithRelationInput!], take: Int, valid: Boolean): [Ticketing_Order!]  # List user orders
}

type Ticketing_ValidationSchemas {
  createPromoInput: JSON!  # Validation schema for creating a promo
  createTicketTierInput: JSON!  # Validation schema for creating a ticket tier
  promoActionDataInput: JSON!  # Validation schema for promo action data
}

type createHelpScoutBeaconPayload {
  helpScoutBeacon: HelpScoutBeacon
}

type createHelpScoutConfigPayload {
  helpScoutConfig: HelpScoutConfig
}

type createHelpScoutCustomFieldPayload {
  helpScoutCustomField: HelpScoutCustomFields
}

type deleteHelpScoutBeaconPayload {
  helpScoutBeacon: HelpScoutBeacon
}

type deleteHelpScoutConfigPayload {
  helpScoutConfig: HelpScoutConfig
}

type deleteHelpScoutCustomFieldPayload {
  helpScoutCustomField: HelpScoutCustomFields
}

type updateHelpScoutBeaconPayload {
  helpScoutBeacon: HelpScoutBeacon
}

type updateHelpScoutConfigPayload {
  helpScoutConfig: HelpScoutConfig
}

type updateHelpScoutCustomFieldPayload {
  helpScoutCustomField: HelpScoutCustomFields
}
```
