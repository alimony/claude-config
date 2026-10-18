# Resident Advisor GraphQL: Mutation fields
Based on the live introspection schema of https://ra.co/graphql (schema snapshot 2026-10-18).

All require authentication. Do not call from an unauthenticated client.

```graphql
  createTicketNotificationsSubscription(eventId: ID!, type: TicketNotificationSubscriptionType): TicketNotificationsSubscription!  # Creates a ticket notifications subscription for the current user
  deleteTicketNotificationsSubscription(eventId: ID!, userId: ID): TicketNotificationsSubscription!  # Deletes a ticket notifications subscription for the current user
  Ticketing_addBasketItems(data: Ticketing_AddBasketItemsInput!, where: Ticketing_BasketWhereUniqueInput!): Ticketing_Basket!  # Add items to a basket by id
  Ticketing_adminUpdateEvent(data: Ticketing_AdminUpdateEventInput!, id: String!): Ticketing_Event!  # Update advanced details of an event
  Ticketing_adminUpdateTicketTier(data: Ticketing_AdminUpdateTicketTierInput!): Ticketing_TicketTierV2!  # Update a ticket tier from admin
  Ticketing_createApplePayMerchantSession(data: Ticketing_CreateMerchantSessionInput!): Ticketing_MerchantSession!  # Validate Apple Pay Merchant
  Ticketing_createBasket(data: Ticketing_CreateBasketInput!): Ticketing_Basket!  # Create basket
  Ticketing_createBasketV2(data: Ticketing_CreateBasketInput!): Ticketing_Basket!  # Create basket
  Ticketing_createCountry(data: Ticketing_CreateCountryInput!): Ticketing_Country!  # Create new country
  Ticketing_createCountryFeeSettings(data: Ticketing_CountryFeeSettingsInput!): Ticketing_CountryFeeSettings!  # Create a country fee setting
  Ticketing_createCurrency(data: Ticketing_CreateCurrencyInput!): Ticketing_Currency!  # Creates currency
  Ticketing_createInvites(data: Ticketing_CreateInvitesInput!): UUID!  # Create a group of single-use invite promo codes
  Ticketing_createOrder(data: Ticketing_CreateOrderInput!): Ticketing_CreateOrderResult!  # Creates order
  Ticketing_createOrderNote(data: Ticketing_CreateOrderNoteInput!): Ticketing_OrderNote!  # Create order note
  Ticketing_createPayPalOrder(data: Ticketing_CreatePayPalOrderInput!): Ticketing_PayPalOrder!  # Create PayPal Order
  Ticketing_createPin(eventId: String!): String!  # Create a new pin
  Ticketing_createPromo(data: Ticketing_CreatePromoInput!): Ticketing_Promo!  # Create promo
  Ticketing_createPromoterFeeSettings(data: Ticketing_PromoterFeeSettingsInput!): Ticketing_PromoterFeeSettings!  # Create a promoter fee setting
  Ticketing_createRefund(data: Ticketing_CreateRefundInput!): Ticketing_Refund!  # Create a refund
  Ticketing_createSavedCard(data: Ticketing_CreateSavedCardInput!): Ticketing_SavedCard!  # Create SavedCard
  Ticketing_createTicketTier(data: Ticketing_CreateTicketTierInput!): Ticketing_TicketTierV2!  # Create a ticket tier
  Ticketing_deleteOrderNote(data: String!): String!  # Delete order note
  Ticketing_deletePin(code: String!): Ticketing_Pin!  # Delete pin
  Ticketing_deletePromo(promoId: String!): Ticketing_Promo!  # Delete promo by its id
  Ticketing_deleteSavedCard(cardToken: String!): Ticketing_SavedCard!  # Delete SavedCard
  Ticketing_deleteTicketTier(id: String!): Ticketing_TicketTierV2!  # Delete a ticket tier
  Ticketing_failOrder(data: Ticketing_FailOrderInput!): Boolean!  # Fail an order by setting its status to failed or cancelled
  Ticketing_importExternalBarcodes(input: Ticketing_ImportExternalBarcodesInput!): Int!  # Import external barcodes from CSV
  Ticketing_invalidateImportedBarcodes(legacyEventId: String!, outlets: [String!]): Ticketing_InvalidateImportedBarcodesResult!  # Invalidate unscanned imported barcodes for an event, optionally limited to the given outlets, returning the number inval
  Ticketing_invalidatePaidBarcodes(input: Ticketing_InvalidatePaidBarcodesInput!): [Ticketing_Barcode!]!  # Invalidate many paid barcodes
  Ticketing_regenerateBarcode(where: Ticketing_BarcodeWhereUniqueInput!): Ticketing_Barcode!  # Regenerate barcode
  Ticketing_removeBasketItem(data: Ticketing_RemoveBasketItemInput!, where: Ticketing_BasketWhereUniqueInput!): Ticketing_Basket!  # Removes an item from a basket by ticket tier id
  Ticketing_resetGlobalSetting(settingName: String!): Ticketing_GlobalSetting!  # Reset global setting by setting name
  Ticketing_resetPromoterSetting(promoterId: String!, settingName: Ticketing_PromoterSettingsNameType!): Ticketing_PromoterSetting!  # Reset promoter setting by promoter id and setting name
  Ticketing_resumePromo(promoId: String!): Ticketing_Promo!  # Resume the sales of a promo
  Ticketing_revalidateBarcodes(where: Ticketing_BarcodeIdWhereInput!): [Ticketing_Barcode!]!  # Revalidate many barcodes
  Ticketing_scannerUpdateBarcodes(data: Ticketing_ScannerRecordBarcodesInput!): [Ticketing_ScanAcknowledgement!]!  # Append scanner actions for last-write-wins resolution. Returns one acknowledgement per submitted scan.
  Ticketing_setGlobalSetting(settingName: String!, settingValue: String!): Ticketing_GlobalSetting!  # Set global setting value
  Ticketing_setPromoterSetting(data: Ticketing_SetPromoterSettingInput!): Ticketing_PromoterSetting!  # Set promoter setting value by promoter id
  Ticketing_startPaymentPlanCheckout(data: Ticketing_StartPaymentPlanCheckoutInput!): Ticketing_PaymentPlanCheckout!  # Start a payment-plan checkout for a basket
  Ticketing_stopPromo(promoId: String!): Ticketing_Promo!  # Stop the sales of a promo
  Ticketing_unmarkOrderItemRefund(where: Ticketing_OrderItemWhereUniqueInput!): Ticketing_OrderItem!  # Unmarks refund status on an order item and regenerates its barcodes
  Ticketing_updateBarcodeTicketHolderName(id: UUID!, ticketHolderName: String!): Ticketing_Barcode!  # Update barcode ticket holder name
  Ticketing_updateBasket(data: Ticketing_UpdateBasketInput!, where: Ticketing_BasketWhereUniqueInput!): Ticketing_Basket!  # Update basket by id
  Ticketing_updateCountryFeeSettings(data: Ticketing_CountryFeeSettingsInput!): Ticketing_CountryFeeSettings!  # Update a country fee setting
  Ticketing_updateOrderNote(data: Ticketing_UpdateOrderNoteInput!): Ticketing_OrderNote!  # Update order note
  Ticketing_updatePaymentPlanStatus(data: Ticketing_UpdatePaymentPlanStatusInput!): Boolean!  # Admin-only: manually update the status of a payment plan
  Ticketing_updatePreviousTicketTier(previousTicketTierId: String, ticketTierId: String!): Ticketing_TicketTierV2!  # Update the previous ticket tier for a ticket tier
  Ticketing_updatePromo(data: Ticketing_UpdatePromoInput!, promoId: String!): Ticketing_Promo!  # Update an existing promo
  Ticketing_updatePromoterFeeDisplayTypes(data: Ticketing_UpdatePromoterFeeDisplayTypes!): Ticketing_PromoterFeeDisplayTypes!  # Update fee display types settings of the promoter
  Ticketing_updatePromoterFeeSettings(data: Ticketing_PromoterFeeSettingsInput!): Ticketing_PromoterFeeSettings!  # Update a promoter fee setting
  Ticketing_updateTicketTier(data: Ticketing_UpdateTicketTierInput!): Ticketing_TicketTierV2!  # Update a ticket tier
  Ticketing_updateTicketTierApprovalStatus(approvalStatus: Ticketing_TicketTierApprovalStatus!, ticketTierIds: [String!]!): [Ticketing_TicketTierV2!]!  # Update the approval status of ticket tiers
  Ticketing_updateTicketTierStopSales(stopSales: Boolean!, ticketTierId: String!): Ticketing_TicketTierV2!  # Stop or resume the sales of a ticket tier
  Ticketing_upsertEventResaleItems(input: Ticketing_UpsertEventResaleItemsInput!): [Ticketing_ResaleItem!]!  # Upsert event resale items
  Ticketing_verifyOrder(data: Ticketing_VerifyOrderInput!): Ticketing_CreateOrderResult!  # Verifies an order
  createBump(input: BumpsInputObject!): BumpsObject
  updateBump(input: BumpsUpdateObject!): BumpsObject!
  createPresale(input: PresaleInput!): Presale!
  deletePresale(input: DeletePresaleInput!): Presale!
  signupToPresale(input: PresaleUsersInput!): PresaleUsers!
  createSourceSavedArtistList(areaId: ID!, countryId: ID, date: DateTime, genres: [String!], ianaTimeZone: String!, latitude: Float, longitude: Float, name: String!): SourceSavedArtistList!  # Creates a saved artist list for a user
  deleteSourceSavedArtist(artistId: ID!): SourceSavedArtist!  # Deletes a saved artist for a user
  deleteSourceSavedArtistList(id: ID!): SourceSavedArtistList!  # deletes a saved artist list for a user
  updateSourceSavedArtistList(areaId: ID!, countryId: ID, date: DateTime, genres: [String!], ianaTimeZone: String!, id: ID!, latitude: Float, longitude: Float, name: String!): SourceSavedArtistList!  # Updates a saved artist list for a user
  updateSourceSavedArtist_SavedArtistList(agentFee: Float, artistId: String!, bookingFee: Float, listId: String!, notes: String, status: SavedArtistListArtistStatus, travelFee: Float): SourceSavedArtist_SavedArtistList!  # Updates a saved artist on a saved artist list
  upsertSourceSavedArtist(artistId: ID!, listIds: [ID!]): SourceSavedArtist!  # Upserts a saved artist for a user
  addGuestlistGuest(input: AddGuestlistGuestInput!): GuestDto!
  deleteGuestlistGuest(input: DeleteGuestlistGuestInput!): GuestDto!
  sendGuestEmail(input: SendGuestEmailInput!): [GuestDto!]!
  makePayment(payment: PaymentInput): String
  generateAuthenticationToken(userToken: String): String
  createPaymentUser(paymentUser: PaymentUserInput!): PaymentUser
  updatePaymentUser(userToken: String!, paymentUser: PaymentUserInput!): PaymentUser
  deletePaymentUser(promoterId: ID): Boolean!
  saveTransferMethodToken(promoterId: ID, transferMethodToken: String): PaymentUser
  deactivateTransferMethodToken(promoterId: ID): PaymentUser
  createFact(expiry: DateTime, resource: AuthorizationObjectInput!, role: String!, subject: AuthorizationObjectInput!): CreatedFact  # Creates new fact
  deleteAllSubjectFacts(subject: AuthorizationObjectInput!): Boolean!  # Deletes all facts of the subject across every resource.
  deleteFacts(resource: AuthorizationObjectInput!, roles: [String!], subject: AuthorizationObjectInput!): Boolean!  # Deletes the specified facts of the subject from the resource. If null is provided for roles, it will delete all facts fo
  replaceFact(currentSubject: AuthorizationObjectInput!, newSubject: AuthorizationObjectInput!, resource: AuthorizationObjectInput!, role: String!): Fact!  # Replaces a role from currentSubject to newSubject
  toggleFollowVenue(venueId: ID, shouldFollow: Boolean!): Venue
  toggleFollowLabel(labelId: ID, shouldFollow: Boolean!): Label
  toggleFollowPromoter(promoterId: ID, shouldFollow: Boolean!): Promoter
  toggleEventInterest(eventId: ID, shouldShowInterest: Boolean!): Event
  toggleFollowArtist(artist: ID, shouldFollow: Boolean!): Artist
  toggleFollowArtists(ids: [ID], shouldFollow: Boolean!): [Artist]
  registerUser(user: UserRegisterInput): RegisteredUserDto
  registerUserApp(user: UserRegisterAppInput): UserRegisteredApp
  convertGuestUser(user: ConvertGuestUserInput): UserRegisteredApp
  verifyUserEmail(oobCode: String): Email
  saveUserAppSettings(appSettings: UserAppSettingsInput): UserAppSettings
  saveUserPushSubscription(userPushSubscriptionInput: UserPushSubscriptionInput): [PushNotification]
  pitch(pitchInput: PitchInput): Boolean
  createEvent(eventInput: EventInput): Event
  createEventRevision(id: ID, eventInput: EventInput, status: EventRevisionApprovedStatusType! = CURRENT): EventRevision
  updateEventRevisionStatus(id: ID, status: EventRevisionApprovedStatusType!): EventRevision
  sendFacebookTestEvent(input: FacebookTestEventInput): Boolean
  sendConversionTestEvent(input: ConversionTestEventInput): Boolean
  upsertTracking(promoterId: ID, trackingEntries: [TrackingEntryInput]): [PromoterTrackingEntry]
  addArtistsToLineup(eventArtists: [EventArtist]): [EventArtistDto]
  removeArtistsFromLineup(eventArtists: [EventArtist]): [EventArtistDto]
  createTicketTier(ticket: TicketTierInput): Ticket
  updateTicketTier(ticket: TicketTierInput): Ticket
  stopTicketTierSales(ticket: TicketTierInput): Ticket
  deleteTicketTier(ticket: TicketTierInput): Boolean!
  subscribeToAllDefaultCommunications(source: MarketingSourceType!): Boolean!
  updateUserMarketingCommunications(updateUserMarketingCommunicationsInput: UpdateUserMarketingCommunicationsInput): [MarketingCommunicationDto]
  createPromoter(promoterInput: PromoterInput): Promoter
  choosePromoter(promoterId: ID, eventId: ID): Event
  updatePromoter(promoterInput: PromoterInput): Promoter
  upsertSetTimes(eventId: ID, lineup: StrippedHtml): Event
  addQueueToEvent(queueId: ID, eventId: ID, startDate: DateTime, displayName: String, promoCode: String): Boolean
  deleteQueueFromEvent(queueId: ID): Boolean
  upsertPromoterVATNumber(promoterId: Int!, vatNumber: String): String
```
