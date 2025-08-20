import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmStyle = 'primary', // 'primary', 'danger', 'warning'
  loading = false
}) => {
  const getConfirmButtonClasses = () => {
    const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-colors';
    
    switch (confirmStyle) {
      case 'danger':
        return `${baseClasses} bg-red-600 text-white hover:bg-red-700 disabled:opacity-50`;
      case 'warning':
        return `${baseClasses} bg-yellow-600 text-white hover:bg-yellow-700 disabled:opacity-50`;
      default:
        return `${baseClasses} bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50`;
    }
  };

  const getIconColor = () => {
    switch (confirmStyle) {
      case 'danger':
        return 'text-red-600';
      case 'warning':
        return 'text-yellow-600';
      default:
        return 'text-blue-600';
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={onClose}
          />

          {/* Modal */}
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                {/* Close button */}
                <button
                  onClick={onClose}
                  className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>

                <div className="sm:flex sm:items-start">
                  {/* Icon */}
                  <div className={`mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full sm:mx-0 sm:h-10 sm:w-10 ${
                    confirmStyle === 'danger' ? 'bg-red-100' :
                    confirmStyle === 'warning' ? 'bg-yellow-100' : 'bg-blue-100'
                  }`}>
                    <ExclamationTriangleIcon 
                      className={`h-6 w-6 ${getIconColor()}`} 
                      aria-hidden="true" 
                    />
                  </div>

                  {/* Content */}
                  <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                    <h3 className="text-base font-semibold leading-6 text-gray-900">
                      {title}
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        {message}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={loading}
                  className={`w-full sm:ml-3 sm:w-auto ${getConfirmButtonClasses()}`}
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Processing...
                    </div>
                  ) : (
                    confirmText
                  )}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  className="mt-3 w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 sm:mt-0 sm:w-auto transition-colors disabled:opacity-50"
                >
                  {cancelText}
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default ConfirmationModal;
