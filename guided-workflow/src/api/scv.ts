import client, { V2_URL } from "~/app/api";
import {
  SuperCustomerListResponseSchema,
  TSuperCustomerForm,
} from "~/domain/SCV";

export const getSuperCustomers = async () => {
  const response = await client.get(`${V2_URL}/manager/scv`);
  return SuperCustomerListResponseSchema.parse(response.data);
};

export const updateSuperCustomer = async (data: TSuperCustomerForm) => {
  const response = await client.put(
    `${V2_URL}/manager/scv/${data.super_customer_id}`,
    data,
  );
  return response.data;
};

export const addSuperCustomer = async (data: TSuperCustomerForm) => {
  const response = await client.post(`${V2_URL}/manager/scv`, data);
  return response.data;
};

export const deleteSuperCustomer = async (super_customer_id: number) => {
  const response = await client.delete(
    `${V2_URL}/manager/scv/${super_customer_id}`,
  );
  return response.data;
};
